
# dg_picks_mlb.py – Versión con total combinado ajustado por ERA del pitcher rival

# [omito parte superior del código por espacio]

        anotadas_home = form_home.get("anotadas", 0)
        recibidas_home = form_home.get("recibidas", 0)
        anotadas_away = form_away.get("anotadas", 0)
        recibidas_away = form_away.get("recibidas", 0)

        def ajustar_por_era(base, era_rival):
            if era_rival < 2.5:
                return base - 0.7
            elif era_rival < 3.5:
                return base - 0.3
            elif era_rival < 4.5:
                return base
            elif era_rival < 5.5:
                return base + 0.5
            else:
                return base + 0.8

        era_away = float(pitcher_away.get("era", 99))
        era_home = float(pitcher_home.get("era", 99))

        ajustado_home = ajustar_por_era(anotadas_home, era_away)
        ajustado_away = ajustar_por_era(anotadas_away, era_home)

        total_combinado = (
            ajustado_home + ajustado_away + recibidas_home + recibidas_away
        ) / 2
