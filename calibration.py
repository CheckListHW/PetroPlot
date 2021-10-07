import os

import lasio
import pandas as pd
import numpy as np
from datetime import datetime


class Model():
    def __init__(self, las_path, Biot=0.85):
        self.las = lasio.read(las_path)
        self.Geomech_Model = pd.DataFrame({'Sv': self.las['SV'], 'SHmax': self.las['SH_MAX_V'],
                                           'Shmin': self.las['SH_MIN_V'], 'Ppore': self.las['PP'], 'Pw': self.las['PW'],
                                           'Well_azimuth': self.las['AZIMUT'],
                                           'Well_deviation': self.las['ZENIT'],
                                           'Poisson_ratio': self.las['POISON'],
                                           'TENSILE_STRENGTH': self.las['TENSILE_STRENGTH'],
                                           'UCS': self.las['CO_BEFORE_CALIBRATION'], 'TVD': self.las['TVD'],
                                           'BIOT': self.las['BIOT'],
                                           'mi': self.las['MI'], 'E': self.las['E'],
                                           'SHmax_azimuth': self.las['SH_MAX_AZIMUTH'],
                                           'BS': self.las['BS'], 'CALIPER': self.las['CALIPER'],
                                           'MUD_DENS': self.las['MUD_DENS']}, index=self.las['DEPT'])

        self.Geomech_Model = self.Geomech_Model.dropna()
        self.Geomech_Model['Biot'] = Biot
        self.progress_iterator = 0

    # классификация скважины по вывалам: 0 - номинальный диаметр/глинистая корка, 1 - вывал, 2 - каверна
    # отсечка каверна/вывал при превышении диаметра на 25% выше номинального (по статистике для рассматриваемых площадей)

    def Breakout_classification(self, Caliper, BS):
        index = self.Geomech_Model.index
        Breakout_classification = np.where(Caliper < BS * 1.03, 0, 1)
        Breakout_classification = np.where(Caliper > BS * 1.25, 2, Breakout_classification)
        Breakout_classification = pd.DataFrame({'Breakout_classification': Breakout_classification}, index=index)

        return Breakout_classification

    # классификация скважины по поглощениям: 0 - нет поглощения, 1 - есть поглощение
    # в текущей версии калибровка скважин без поглощений
    def Mud_loss_classify(self, Breakout_classification):
        index = self.Geomech_Model.index
        Mud_loss_classification = pd.DataFrame(
            {'Mud_loss_classification': Breakout_classification.Breakout_classification},
            index=index)
        Mud_loss_classification[:] = 0

        return Mud_loss_classification

    # рассчет компонентов тензора ПОЛНЫХ напряжений в плоскости скважины (трансформация тензора полных напряжений)
    # z-вдоль ствола скважины, 
    # x-в направлении нижней стенки скважины, 
    # y-90° против часовой стрелки от x, ось y находится в горизонтальной плоскости):

    # входные данные - напряжения и траектория скважины в порядке (Sv, SHmax, Shmin, Well_azimuth, Well_deviation)
    # результат - компоненты тензора напряжений в плоскости скважины

    def Transform_Stress(self, Sv, SHmax, Shmin, SHmax_azimuth, Well_azimuth_input, Well_deviation_input, Degrees=True):
        index = self.Geomech_Model.index
        Azimuth_from_SHmax = np.where(Well_azimuth_input > SHmax_azimuth,
                                      360 - (Well_azimuth_input - SHmax_azimuth), SHmax_azimuth - Well_azimuth_input)
        Well_azimuth = np.deg2rad(Well_azimuth_input)
        Well_deviation = np.deg2rad(Well_deviation_input)

        if not Degrees:
            Well_azimuth = Well_azimuth_input
            Well_deviation = Well_deviation_input
            Azimuth_from_SHmax = np.where(Well_azimuth_input > SHmax_azimuth,
                                          2 * np.pi - (Well_azimuth_input - SHmax_azimuth),
                                          SHmax_azimuth - Well_azimuth_input)

        lxx = np.cos(Well_azimuth) * np.cos(Well_deviation)
        lxy = np.sin(Well_azimuth) * np.cos(Well_deviation)
        lxz = -np.sin(Well_deviation)
        lyx = -np.sin(Well_azimuth)
        lyy = np.cos(Well_azimuth)
        lyz = 0
        lzx = np.cos(Well_azimuth) * np.sin(Well_deviation)
        lzy = np.sin(Well_azimuth) * np.sin(Well_deviation)
        lzz = np.cos(Well_deviation)
        Sxo = lxx ** 2 * SHmax + lxy ** 2 * Shmin + lxz ** 2 * Sv
        Syo = lyx ** 2 * SHmax + lyy ** 2 * Shmin + lyz ** 2 * Sv
        Szo = lzx ** 2 * SHmax + lzy ** 2 * Shmin + lzz ** 2 * Sv
        txyo = lxx * lyx * SHmax + lxy * lyy * Shmin + lxz * lyz * Sv
        tyzo = lyx * lzx * SHmax + lyy * lzy * Shmin + lyz * lzz * Sv
        tzxo = lzx * lxx * SHmax + lzy * lxy * Shmin + lzz * lxz * Sv

        Transformed_df = pd.DataFrame({'Sxo': Sxo, 'Syo': Syo,
                                       'Szo': Szo, 'txyo': txyo, 'tyzo': tyzo,
                                       'tzxo': tzxo}, index=index)
        return Transformed_df

    # рассчет ЭФФЕКТИВНЫХ напряжений на стенке скважины с посмощью уравнения Кирша для точки с углом 0° от оси x
    # против часовой стрелки
    # поскольку радиальное напряжение не меняется для разных углов - рассчитывается только одно значение
    # a,b,c,d,e - временные переменные для суммирования столбиков значений

    # входные данные - напряжения, трансформированные на стенку скважины, поровое давление, давление в скважине, коэфф Пуассона
    # (Sxo, Syo, Szo, txyo, tyzo, tzxo, Ppore, Pw, Poisson_ratio)

    # результат - (St_x_df, Sz_x_df, Ttz_x_df) напряжения тангенсальное, вертикальное и касательное на стенке скважины
    # (Smax_x_df, Smin_x_df) линеаризованные напряжения на стенке скважины
    # i_max_df  -  направление максимального тангенсального напряжения
    # (S_1_df, S_2_df, S_3_df) - главные напряжения для всех глубин и углов

    def Kirsch_Wall(self, Sxo, Syo, Szo, txyo, tyzo, tzxo, Ppore, Pw, Poisson_ratio):
        index = self.Geomech_Model.index
        i = 0
        Sr = Pw - Ppore
        a = Sxo + Syo - 2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) - 4 * txyo * np.sin(2 * np.radians(i)) - Pw - Ppore
        b = Szo - Poisson_ratio * (
                    2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) + 4 * txyo * np.sin(2 * np.radians(i))) - Ppore
        c = 2 * (-tzxo * np.sin(np.radians(i)) + tyzo * np.cos(np.radians(i)))
        d = 0.5 * (b + a + ((b - a) ** 2 + 4 * (c ** 2)) ** 0.5)
        e = 0.5 * (b + a - ((b - a) ** 2 + 4 * (c ** 2)) ** 0.5)
        f = Sr

        # рассчет напряжений на стенке скважины с посмощью уравнения Кирша для точек с углами 1-179° от оси x против часовой стрелки
        # угол 180° - представлен углом 0°
        for i in range(1, 180):
            St_x = Sxo + Syo - 2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) - 4 * txyo * np.sin(
                2 * np.radians(i)) - Pw - Ppore
            Sz_x = Szo - Poisson_ratio * (
                        2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) + 4 * txyo * np.sin(2 * np.radians(i))) - Ppore
            Ttz_x = 2 * (-tzxo * np.sin(np.radians(i)) + tyzo * np.cos(np.radians(i)))
            Smax_x = 0.5 * (Sz_x + St_x + (((Sz_x - St_x) ** 2) + 4 * (Ttz_x ** 2)) ** 0.5)
            Smin_x = 0.5 * (Sz_x + St_x - (((Sz_x - St_x) ** 2) + 4 * (Ttz_x ** 2)) ** 0.5)

            a = np.column_stack((a, St_x))
            b = np.column_stack((b, Sz_x))
            c = np.column_stack((c, Ttz_x))
            d = np.column_stack((d, Smax_x))
            e = np.column_stack((e, Smin_x))
            f = np.column_stack((f, Sr))

        # итоговыe напряжения на стенке скважины с индексами [глубина, угол от 0 до 179]:

        St_x_df = pd.DataFrame(a, index=index)
        Sz_x_df = pd.DataFrame(b, index=index)
        Ttz_x_df = pd.DataFrame(c, index=index)
        Smax_x_df = pd.DataFrame(d, index=index)
        Smin_x_df = pd.DataFrame(e, index=index)
        Sr = pd.DataFrame(f, index=index)

        return St_x_df, Sz_x_df, Ttz_x_df, Smax_x_df, Smin_x_df, Sr

        # определение (выбор или сортировка) ЭФФЕКТИВНЫХ главных нормальных напряжений на стенке скважины:

    def Principal_Stresses(self, Smax_x, Smin_x, Sr):
        index = self.Geomech_Model.index
        S_1 = np.where(Smax_x > Sr, Smax_x, Sr)
        S_1 = np.where(Smin_x > S_1, Smin_x, S_1)
        S_1 = pd.DataFrame(S_1, index=index)

        S_2 = np.where(Smin_x < Smax_x, np.where(Smin_x > Sr, Smin_x, Sr), False)
        S_2 = pd.DataFrame(S_2, index=index)

        S_3 = np.where(Smax_x < Sr, Smax_x, Sr)
        S_3 = np.where(Smin_x < S_3, Smin_x, S_3)
        S_3 = pd.DataFrame(S_3, index=index)

        # определение углов где действуют максимальные напряжения:
        i_max = pd.DataFrame({0: Smax_x.idxmax(axis=1)}, index=index)
        for i in range(1, 91):
            i_max[i] = np.where(i_max[0] + i > 179, i_max[0] + i - 180, i_max[0] + i)

        return S_1, S_2, S_3, i_max

        # сортировка напряжений относительно точки с максимальным тангенсальным напряжением:

    def sort_i_max(self, Smax_x, Smin_x, i_max, S_1, S_3):
        index = self.Geomech_Model.index
        Smax_x_i = pd.DataFrame({0: Smax_x.lookup(i_max.index, i_max[0])}, index=index)
        Smin_x_i = pd.DataFrame({0: Smin_x.lookup(i_max.index, i_max[0])}, index=index)
        S_1_i = pd.DataFrame({0: S_1.lookup(i_max.index, i_max[0])}, index=index)
        S_3_i = pd.DataFrame({0: S_3.lookup(i_max.index, i_max[0])}, index=index)
        for i in range(1, 91):
            Smax_x_i[i] = Smax_x.lookup(i_max.index, i_max[i])
            Smin_x_i[i] = Smin_x.lookup(i_max.index, i_max[i])
            S_1_i[i] = S_1.lookup(i_max.index, i_max[i])
            S_3_i[i] = S_3.lookup(i_max.index, i_max[i])

        return Smax_x_i, Smin_x_i, S_1_i, S_3_i

    # Определение угла вывала с помощью критерия Кулона
    # входные данные - максимальное и минимальное эффективные главные нормальные напряжения, прочность на одноосное сжатие
    # и тангенс угла внутреннего трения

    # результат - угол вывала на стенке скважины

    def Coulumb_breakout(self, S_1, S_3, UCS, mi, Smax_x_i, Ppore, TVD):
        index = self.Geomech_Model.index
        k_factor = pd.DataFrame(((mi ** 2 + 1) ** 0.5 + mi) ** 2, index=index)
        UCS = pd.DataFrame(UCS, index=index)
        Ppore = pd.DataFrame(Ppore, index=index)
        TVD = pd.DataFrame(TVD, index=index)
        for x in range(1, 180):
            k_factor[x] = k_factor[0]
            UCS[x] = UCS[0]
            Ppore[x] = Ppore[0]
            TVD[x] = TVD[0]
        Breakout = pd.DataFrame(np.where(S_1 > UCS + k_factor * S_3, 1, 0), index=index)
        Breakout_probability = pd.DataFrame(S_1 - UCS + k_factor * S_3, index=index)
        Breakout_angle = pd.DataFrame({'Breakout_angle': Breakout.sum(axis=1)}, index=index)
        Breakout_grad = ((Smax_x_i - UCS.loc[:, :90]) / (k_factor.loc[:, :90]) + Ppore.loc[:, :90]) / (
                    TVD.loc[:, :90] * 9.81) * 1000

        return Breakout_angle, Breakout_grad, Breakout_probability

    # определение градиентов ГНВП и поглощений
    # входные данные - (S_3, Shmin, Ppore, TVD, Tensile_strength)

    # результат - градиенты ГНВП и поглощений

    def Pore_Loss(self, S_3, Shmin, Ppore, TVD, Tensile_strength):
        index = self.Geomech_Model.index

        Pore_grad = Ppore / 9.81 / TVD * 1000
        Tensile_frac_grad = (S_3.min(axis=1) + Ppore + Tensile_strength) / 9.81 / TVD * 1000
        Mud_loss_grad = Shmin / 9.81 / TVD * 1000

        Pore_Loss_Grad = pd.DataFrame({'Pore_grad': Pore_grad, 'Tensile_frac_grad': Tensile_frac_grad,
                                       'Mud_loss_grad': Mud_loss_grad}, index=index)

        return Pore_Loss_Grad

    def Solve(self, Sv, SHmax, Shmin, SHmax_azimuth, Ppore, Pw, Poisson_ratio, UCS, mi,
              Tensile_Strength, Well_azimuth_input, Well_deviation_input, TVD):

        self.progress_iterator += 1
        #            print(self.progress_iterator)

        Transformed_Stress = self.Transform_Stress(Sv=Sv, SHmax=SHmax, Shmin=Shmin, SHmax_azimuth=SHmax_azimuth,
                                                   Well_azimuth_input=Well_azimuth_input,
                                                   Well_deviation_input=Well_deviation_input, Degrees=True)

        St_x, Sz_x, Ttz_x, Smax_x, Smin_x, Sr = self.Kirsch_Wall(
            Sxo=Transformed_Stress.Sxo.values, Syo=Transformed_Stress.Syo.values,
            Szo=Transformed_Stress.Szo.values, txyo=Transformed_Stress.txyo.values,
            tyzo=Transformed_Stress.tyzo.values, tzxo=Transformed_Stress.tzxo.values,
            Ppore=Ppore, Pw=Pw, Poisson_ratio=Poisson_ratio)

        S_1, S_2, S_3, i_max = self.Principal_Stresses(Smax_x, Smin_x, Sr)

        Smax_x_i, Smin_x_i, S_1_i, S_3_i = self.sort_i_max(Smax_x, Smin_x, i_max, S_1, S_3)

        Breakout_angle, Breakout_grad, Breakout_probability = self.Coulumb_breakout(S_1, S_3, UCS, mi,
                                                                                    Smax_x_i, Ppore, TVD)

        Pore_Loss_Grad = self.Pore_Loss(S_3, Shmin, Ppore, TVD, Tensile_Strength)

        return Breakout_angle, Breakout_grad, Pore_Loss_Grad, Smax_x_i, S_3_i

    def define_success(self, ratio, Geomech_Model, Breakout_classification,
                       Mud_loss_classification, Breakout_grad, Pore_Loss_Grad):

        index = self.Geomech_Model.index
        df = pd.DataFrame({'Mud_dens': self.Geomech_Model.MUD_DENS,
                           'Breakout_classification': Breakout_classification.Breakout_classification,
                           'Mud_loss_classification': Mud_loss_classification.Mud_loss_classification}, index=index)

        df['Breakout_grad_0_' + str(ratio)] = Breakout_grad[0]
        df['Breakout_grad_90_' + str(ratio)] = Breakout_grad[90]
        df['Mud_loss_grad' + str(ratio)] = Pore_Loss_Grad['Mud_loss_grad']

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Breakout_grad_0_' + str(ratio)]) &
                                                (df['Breakout_classification'] == 0)), 1, 0)

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                (df['Mud_dens'] > df['Breakout_grad_90_' + str(ratio)]) &
                                                (df['Breakout_classification'] == 1)), 1, df['Success_' + str(ratio)])

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                (df['Mud_dens'] < df['Breakout_grad_90_' + str(ratio)]) &
                                                (df['Breakout_classification'] == 2)), 1, df['Success_' + str(ratio)])

        df['Success_' + str(ratio)] = np.where((df['Breakout_classification'] == 3), np.nan,
                                               df['Success_' + str(ratio)])

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Mud_loss_grad' + str(ratio)]) &
                                                (df['Mud_loss_classification'] == 0)), 0, df['Success_' + str(ratio)])

        Success = df['Success_' + str(ratio)].sum() / df['Success_' + str(ratio)].count() * 100

        return Success

    def Define_Strains(self, Breakout_classification, Mud_loss_classification,
                       MD, Pc, start_ratio=1.00, stop_ratio=1.20, step=0.01):

        index = self.Geomech_Model.index
        df = pd.DataFrame({'v': self.Geomech_Model.Poisson_ratio, 'Sv': self.Geomech_Model.Sv,
                           'Pp': self.Geomech_Model.Ppore, 'Sv': self.Geomech_Model.Sv,
                           'v': self.Geomech_Model.Poisson_ratio, 'E': self.Geomech_Model.E * 1000,
                           'Mud_dens': self.Geomech_Model.MUD_DENS,
                           'Breakout_classification': Breakout_classification.Breakout_classification,
                           'Mud_loss_classification': Mud_loss_classification.Mud_loss_classification}, index=index)

        v = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Poisson_ratio'].values[0]
        E = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'E'].values[0] * 1000
        Pp = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Ppore'].values[0]
        Sv = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Sv'].values[0]
        Biot = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Biot'].values[0]

        Strain_max_list = np.array([])
        Strain_min_list = np.array([])
        Success_list = np.array([])

        ratio_list = [round(i, 2) for i in np.arange(start_ratio, stop_ratio + step, step)]
        for ratio in ratio_list:
            Spoison = v * Sv / (1 - v) - v * Biot * Pp / (1 - v) + Biot * Pp
            Strain_max = (Pc - Spoison * (1 - 1 / v) - (Pc * ratio) / v) / ((v - 1 / v) * E / (1 - v ** 2))
            Strain_min = (Pc * ratio - Spoison - E / (1 - v ** 2) * Strain_max) / (v * E / (1 - v ** 2))

            df['Shmin_ratio_' + str(ratio)] = (
                        df['v'] * df['Sv'] / (1 - df['v']) - df['v'] * Biot * df['Pp'] / (1 - df['v']) + Biot * df[
                    'Pp'] +
                        df['E'] * Strain_min / (1 - df['v'] ** 2) + df['v'] * df['E'] * Strain_max / (1 - df['v'] ** 2))
            df['SHmax_ratio_' + str(ratio)] = (
                        df['v'] * df['Sv'] / (1 - df['v']) - df['v'] * Biot * df['Pp'] / (1 - df['v']) + Biot * df[
                    'Pp'] +
                        df['E'] * Strain_max / (1 - df['v'] ** 2) + df['v'] * df['E'] * Strain_min / (1 - df['v'] ** 2))

            Breakout_angle, Breakout_grad, Pore_Loss_Grad, Smax_x_i, S_3_i = self.Solve(
                SHmax=df['SHmax_ratio_' + str(ratio)].values,
                Shmin=df['Shmin_ratio_' + str(ratio)].values,
                Sv=self.Geomech_Model.Sv.values,
                SHmax_azimuth=self.Geomech_Model.SHmax_azimuth.values,
                Ppore=self.Geomech_Model.Ppore.values,
                Pw=self.Geomech_Model.Pw.values,
                Poisson_ratio=self.Geomech_Model.Poisson_ratio.values,
                UCS=self.Geomech_Model.UCS.values,
                mi=self.Geomech_Model.mi.values,
                Tensile_Strength=self.Geomech_Model.TENSILE_STRENGTH.values,
                Well_azimuth_input=self.Geomech_Model.Well_azimuth.values,
                Well_deviation_input=self.Geomech_Model.Well_deviation.values,
                TVD=self.Geomech_Model.TVD.values)

            df['Breakout_grad_0_' + str(ratio)] = Breakout_grad[0]
            df['Breakout_grad_90_' + str(ratio)] = Breakout_grad[90]
            df['Mud_loss_grad' + str(ratio)] = Pore_Loss_Grad['Mud_loss_grad']

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Breakout_grad_0_' + str(ratio)]) &
                                                    (df['Breakout_classification'] == 0)), 1, 0)

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                    (df['Mud_dens'] > df['Breakout_grad_90_' + str(ratio)]) &
                                                    (df['Breakout_classification'] == 1)), 1,
                                                   df['Success_' + str(ratio)])

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                    (df['Mud_dens'] < df['Breakout_grad_90_' + str(ratio)]) &
                                                    (df['Breakout_classification'] == 2)), 1,
                                                   df['Success_' + str(ratio)])

            df['Success_' + str(ratio)] = np.where((df['Breakout_classification'] == 3), np.nan,
                                                   df['Success_' + str(ratio)])

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Mud_loss_grad' + str(ratio)]) &
                                                    (df['Mud_loss_classification'] == 0)), 0,
                                                   df['Success_' + str(ratio)])

            Success = df['Success_' + str(ratio)].sum() / df['Success_' + str(ratio)].count() * 100

            Strain_max_list = np.append(Strain_max_list, float(Strain_max))
            Strain_min_list = np.append(Strain_min_list, float(Strain_min))
            Success_list = np.append(Success_list, float(Success))

        ratio_list = np.array(ratio_list)

        ratio_frame = pd.DataFrame({'ratio': ratio_list, 'Success': Success_list,
                                    'Strain_max': Strain_max_list, 'Strain_min': Strain_min_list})

        best_ratio = ratio_frame.loc[ratio_frame['Success'].idxmax(), 'ratio']
        best_SHmax = df['SHmax_ratio_' + str(best_ratio)]
        best_Shmin = df['Shmin_ratio_' + str(best_ratio)]

        return ratio_frame, best_ratio, best_SHmax, best_Shmin

    def UCS_calibrate(self, Co, mi, Caliper, BS, Breakout_classification, Mud_dens,
                      Breakout_grad, Smax_x_i, S_3_i):

        index = self.Geomech_Model.index
        Co = pd.DataFrame({'Co': Co}, index=index)
        k_factor = pd.DataFrame({'k_factor': ((mi ** 2 + 1) ** 0.5 + mi) ** 2}, index=index)
        Caliper = pd.DataFrame({'Caliper': Caliper}, index=index)
        Mud_dens = pd.DataFrame({'Mud_dens': Mud_dens}, index=index)
        Breakout_grad_0 = pd.DataFrame({'Breakout_grad_0': Breakout_grad[0]}, index=index)
        Breakout_grad_45 = pd.DataFrame({'Breakout_grad_45': Breakout_grad[45]}, index=index)
        S_3_i_0 = pd.DataFrame({'S_3_i_0': S_3_i[0]}, index=index)
        S_3_i_45 = pd.DataFrame({'S_3_i_45': S_3_i[0]}, index=index)
        Smax_x_0 = pd.DataFrame({'Smax_x_0': Smax_x_i[0]}, index=index)
        Smax_x_45 = pd.DataFrame({'Smax_x_45': Smax_x_i[45]}, index=index)

        df = pd.concat([k_factor, Mud_dens, Co, BS, Breakout_classification,
                        Breakout_grad_0, Breakout_grad_45,
                        Smax_x_0, Smax_x_45, Caliper, S_3_i_0, S_3_i_45], axis=1)

        df['dC_0'] = df['Co'] + df['k_factor'] * df['S_3_i_0'] - df['Smax_x_0']
        df['dC_90'] = df['Co'] + df['k_factor'] * df['S_3_i_45'] - df['Smax_x_45']
        df['dC_1'] = df['dC_0'] + (df['dC_90'] - df['dC_0']) * (df['Caliper'] - df['BS']) / (df['BS'] * 1.25)
        df['dC_2'] = df['dC_90'] + (df['dC_0'] - df['dC_90']) / 2

        df['Co_calibrated'] = np.where((df['Mud_dens'] > df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 0), df['Co'] - df['dC_0'] * 0.8, df['Co'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] > df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 1), df['Co'] - df['dC_1'], df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] < df['Breakout_grad_45']) &
                                       (df['Breakout_classification'] == 1), df['Co'] - df['dC_2'], df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] < df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 0), df['Co'] - df['dC_0'] * 1.1,
                                       df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] > df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 2), df['Co'] - df['dC_90'] * 1.1,
                                       df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] < df['Breakout_grad_45']) &
                                       (df['Breakout_classification'] == 0), df['Co'] - df['dC_0'] * 1.1,
                                       df['Co_calibrated'])
        df['Co_calibrated'] = np.where(
            (df['Mud_dens'] < df['Breakout_grad_0']) & (df['Mud_dens'] > df['Breakout_grad_45']) &
            (df['Breakout_classification'] == 2), df['Co'] + df['dC_2'] * 1.1, df['Co_calibrated'])

        df['Co_confirmed'] = np.where((df['Breakout_classification'] == 1) |
                                      (df['Breakout_classification'] == 2), df['Co_calibrated'], np.nan)
        df['Co_possible'] = np.where((df['Breakout_classification'] == 0), df['Co_calibrated'], np.nan)

        return df

    def Calibrate(self, MD=3388, Pc=60.37):

        Geomech_Model = self.Geomech_Model
        Caliper = self.Geomech_Model.CALIPER.values
        BS = self.Geomech_Model.BS.values

        Breakout_classification = self.Breakout_classification(Caliper=Caliper, BS=BS)
        Mud_loss_classification = self.Mud_loss_classify(Breakout_classification)

        ratio_frame, best_ratio, best_SHmax, best_Shmin = self.Define_Strains(
            Breakout_classification=Breakout_classification,
            Mud_loss_classification=Mud_loss_classification,
            MD=MD, Pc=Pc, start_ratio=1.00,
            stop_ratio=1.20, step=0.01)
        (Breakout_angle_strain_calibrated, Breakout_grad_strain_calibrated,
         Pore_Loss_Grad_strain_calibrated, Smax_x_i_strain_calibrated,
         S_3_i_strain_calibrated) = self.Solve(SHmax=best_SHmax.values,
                                               Shmin=best_Shmin.values,
                                               Sv=self.Geomech_Model.Sv.values,
                                               SHmax_azimuth=self.Geomech_Model.SHmax_azimuth.values,
                                               Ppore=self.Geomech_Model.Ppore.values,
                                               Pw=self.Geomech_Model.Pw.values,
                                               Poisson_ratio=self.Geomech_Model.Poisson_ratio.values,
                                               UCS=self.Geomech_Model.UCS.values,
                                               mi=self.Geomech_Model.mi.values,
                                               Tensile_Strength=self.Geomech_Model.TENSILE_STRENGTH.values,
                                               Well_azimuth_input=self.Geomech_Model.Well_azimuth.values,
                                               Well_deviation_input=self.Geomech_Model.Well_deviation.values,
                                               TVD=self.Geomech_Model.TVD.values)

        UCS_calibrated = self.UCS_calibrate(Co=self.Geomech_Model.UCS, mi=self.Geomech_Model.mi,
                                            Caliper=self.Geomech_Model.CALIPER, BS=self.Geomech_Model.BS,
                                            Breakout_classification=Breakout_classification,
                                            Mud_dens=self.Geomech_Model.MUD_DENS,
                                            Breakout_grad=Breakout_grad_strain_calibrated,
                                            Smax_x_i=Smax_x_i_strain_calibrated, S_3_i=S_3_i_strain_calibrated)

        (Breakout_angle_calibrated,
         Breakout_grad_calibrated,
         Pore_Loss_Grad_calibrated,
         Smax_x_i_calibrated,
         S_3_i_calibrated) = self.Solve(SHmax=best_SHmax.values,
                                        Shmin=best_Shmin.values,
                                        UCS=UCS_calibrated['Co_calibrated'].values,
                                        Sv=self.Geomech_Model.Sv.values,
                                        SHmax_azimuth=self.Geomech_Model.SHmax_azimuth.values,
                                        Ppore=self.Geomech_Model.Ppore.values,
                                        Pw=self.Geomech_Model.Pw.values,
                                        Poisson_ratio=self.Geomech_Model.Poisson_ratio.values,
                                        mi=self.Geomech_Model.mi.values,
                                        Tensile_Strength=self.Geomech_Model.TENSILE_STRENGTH.values,
                                        Well_azimuth_input=self.Geomech_Model.Well_azimuth.values,
                                        Well_deviation_input=self.Geomech_Model.Well_deviation.values,
                                        TVD=self.Geomech_Model.TVD.values)

        Success = self.define_success(ratio=best_ratio, Geomech_Model=self.Geomech_Model,
                                      Breakout_classification=Breakout_classification,
                                      Mud_loss_classification=Mud_loss_classification,
                                      Breakout_grad=Breakout_grad_calibrated,
                                      Pore_Loss_Grad=Pore_Loss_Grad_calibrated)

        self.Geomech_Model['SHmax_calibrated'] = best_SHmax.values
        self.Geomech_Model['Shmin_calibrated'] = best_Shmin.values
        self.Geomech_Model['UCS_calibrated'] = UCS_calibrated['Co_calibrated'].values
        self.Success = Success
        self.Ratio = best_ratio

        return Success

    def Write_Results(self, results_path):
        las = lasio.LASFile()
        las.well.DATE = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        las.other = 'Output file from Geomechanics Calibration v1 by Dmitry Konoshonkin'
        las.add_curve('DEPT', self.Geomech_Model.index, unit='m')
        las.add_curve('SHmax_calibrated', self.Geomech_Model['SHmax_calibrated'], unit='MPa')
        las.add_curve('Shmin_calibrated', self.Geomech_Model['Shmin_calibrated'], unit='MPa')
        las.add_curve('UCS_calibrated', self.Geomech_Model['UCS_calibrated'], unit='MPa')
        las.write(results_path, version=2)


from tkinter import Tk
import tkinter as tk
import queue
import threading
from tkinter import *
from tkinter.ttk import *
from tkinter.scrolledtext import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showerror

window = tk.Tk()
window.title('Автокалибровка v1.0')

models = []
q = queue.Queue()


def Open_Model(self):
    filename = askopenfilename()
    try:
        Geomech_Model = Model(las_path=filename)
        Model_path.insert(0, filename)
        models.clear()
        models.append(Geomech_Model)
        tf = open(filename)
        data = tf.read()
        Preview.delete('0.0', END)
        Preview.insert(END, data)
        tf.close()
    except:
        showerror(title='Ошибка входных данных', message='Проверьте входные данные и повторите попытку')


def Calibrate_Model():
    try:
        Pc_value = float(Pc_Entry.get())
        Pc_depth_value = float(Pc_depth_Entry.get())
        progress.start()
        models[0].Calibrate(MD=Pc_depth_value, Pc=Pc_value)
        Success_results.insert(0, np.round(models[0].Success, 1))
        Ratio_results.insert(0, models[0].Ratio)
    except:
        showerror(title='Ошибка расчета', message='Проверьте входные данные и повторите попытку')


def Save_Model(self):
    try:
        results_path = asksaveasfilename(defaultextension='.las')
        models[0].Write_Results(results_path=results_path)
        Save_path.insert(0, results_path)
        tf = open(results_path)
        data = tf.read()
        Preview.delete('0.0', END)
        Preview.insert(END, data)
        tf.close()
    except:
        showerror(title='Ошибка сохранения', message='Не могу сохранить результаты')


def tb_click(self):
    ThreadedTask(q).start()
    window.after(100, process_queue)


def process_queue():
    try:
        msg = q.get(0)
        # Show result of the task if needed
        progress.stop()
        progress['mode'] = 'determinate'
        progress['value'] = 100
        if Success_results.get() == '':
            progress['value'] = 0
            progress['mode'] = 'determinate'
    except queue.Empty:
        window.after(100, process_queue)


class ThreadedTask(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q

    def run(self):
        Calibrate_Model()  # Simulate long running process
        self.q.put('Task finished')


# Parent widget for the buttons
Mainframe = Frame(window)
Mainframe.grid(row=0, column=0, padx=(5), pady=(5), sticky=N + W)

buttons_frame = LabelFrame(Mainframe, text='Входные данные')
buttons_frame.grid(row=0, column=0, padx=(5), sticky=N + W)

buttons_frame2 = LabelFrame(Mainframe, text='Калибровка')
buttons_frame2.grid(row=0, column=1, padx=(5), sticky=N + W)

buttons_frame3 = LabelFrame(Mainframe, text='Дополнительно')
buttons_frame3.grid(row=0, column=2, padx=(5), sticky=N + W)

Open_btn_line = Button(buttons_frame3, text='Просмотр кривых')
Open_btn_line.grid(column=0, row=0, sticky=W + E, ipady=1, pady=1)

Open_btn = Button(buttons_frame, text='Открыть модель')
Open_btn.grid(column=0, row=0, sticky=W + E, ipady=1, pady=1)

Model_path = Entry(buttons_frame, width=50)
Model_path.grid(column=1, row=0, sticky=W + E, ipady=1, pady=1)

Pc_label = Label(buttons_frame, anchor='e', justify=RIGHT, width=27,
                 text='Pc [МПа]:').grid(column=0, row=1, ipady=1, pady=1)

Pc_Entry = Entry(buttons_frame, width=15)
Pc_Entry.grid(column=1, row=1, sticky=W, ipady=1, pady=1)

Pc_depth_label = Label(buttons_frame, anchor='e', justify=LEFT, width=27,
                       text='Глубина ГРП [MD, м]:').grid(column=0, row=2, ipady=1, pady=1)

Pc_depth_Entry = Entry(buttons_frame, width=15)
Pc_depth_Entry.grid(column=1, row=2, sticky=W, ipady=1, pady=1)

Calibrate_btn = Button(buttons_frame2, text='Провести калибровку')
Calibrate_btn.grid(column=0, row=0, ipady=1, pady=1)

progress = Progressbar(buttons_frame2, orient=HORIZONTAL, length=320, mode='indeterminate')
progress.grid(column=1, row=0, columnspan=2, ipady=1, pady=1)

Success_label = Label(buttons_frame2, anchor='e', justify=LEFT, width=27,
                      text='Сходимость, %:').grid(column=0, row=2, ipady=1, pady=1)

Success_results = Entry(buttons_frame2, width=15)
Success_results.grid(column=1, row=2, sticky=W, ipady=1, pady=1)

Ratio_label = Label(buttons_frame2, anchor='e', justify=LEFT, width=27,
                    text='Соотношение напряжений:').grid(column=0, row=3, ipady=1, pady=1)

Ratio_results = Entry(buttons_frame2, width=15)
Ratio_results.grid(column=1, row=3, sticky=W, ipady=1, pady=1)

Save_btn = Button(buttons_frame2, text='Сохранить результат')
Save_btn.grid(column=0, row=4, ipady=1, pady=1)

Save_path = Entry(buttons_frame2, width=50)
Save_path.grid(column=1, row=4, sticky=W + E, ipady=1, pady=1)



from petro_chart import Window

# Group1 Frame ----------------------------------------------------


notebook = Notebook(window)
notebook.grid(row=1, column=0, padx=(5), pady=0, columnspan=2, sticky=E + S + N + W)


group1 = Frame(notebook)

group2 = Frame(notebook)

group3 = Frame(notebook)

if not os.path.isdir(os.getcwd() + '/Files'):
    os.mkdir(os.getcwd() + '/Files')

enter_template_name = 'Files/planshet_s_vhodnymi_dannymi(shablon).json'
result_template_name = 'Files/rezultaty_kalibrovki(shablon).json'

open(enter_template_name, 'a').close()
open(result_template_name, 'a').close()

petro_chart_enter = Window(group2, template=enter_template_name)
petro_chart_res = Window(group3, template=result_template_name)

notebook.add(group1, text='Предварительный просмотр las файлов')
notebook.add(group2, text='Планшет с входными данными')
notebook.add(group3, text='Результаты калибровки')

window.columnconfigure(0, weight=1)
window.rowconfigure(1, weight=1)

group1.rowconfigure(0, weight=1)
group1.columnconfigure(0, weight=1)

Preview = ScrolledText(group1, wrap=WORD)
Preview.grid(column=0, row=0, sticky=E + S + N + W)


def open_window(args):
    root = Tk()
    Window(root)

Open_btn.bind('<Button-1>', Open_Model)
Open_btn_line.bind('<Button-1>', open_window)
Calibrate_btn.bind('<Button-1>', tb_click)
Save_btn.bind('<Button-1>', Save_Model)

window.mainloop()
