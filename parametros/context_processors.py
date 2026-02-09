def empresa_theme(request):
    theme = {
        "primary": "#048B36",
        "primary_dark": "#03682A",
        "accent": "#18B85A",
        "sidebar": "#03140A",
    }

    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        perfil = getattr(user, "perfil", None)
        empresa = getattr(perfil, "empresa", None)
        if empresa:
            theme = {
                "primary": getattr(empresa, "color_primary", theme["primary"]),
                "primary_dark": getattr(empresa, "color_primary_dark", theme["primary_dark"]),
                "accent": getattr(empresa, "color_accent", theme["accent"]),
                "sidebar": getattr(empresa, "color_sidebar", theme["sidebar"]),
            }

    return {"EMPRESA_THEME": theme}
