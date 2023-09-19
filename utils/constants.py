# Note: pluginName should ideally match the top level directory name for the plugin
pluginEnv = {
    "pluginName":       "reStAssured",
    "docsWeb":          "",
    "doDebug":          True,
    # "pluginMainReloadModule": "",
    # "reloadPluginWhenTheseSettingsChange": [""],
    # "reloadPluginWhenAnySettingsChange": False,
}

pluginSettingsGovernor = {
    "ID": {
        "outputDictDesc": (f"{pluginEnv.get('pluginName', 'UnNamed-Plugin')} combined Plugin Settings "
                            "(from settings file() and project settings)")
    },
    "Settings": {
        # "browserCmd"            : {"default": ["google-chrome", "--incognito", "-open"], "checks": ["is_str_or_list"]},
        # "ignoreBrowserErrs"     : {"default": False, "checks": ["is_bool"]},
        # "openHtmlTargets"       : {"default": {"Sphinx Build Folder": "_build/html"}, "checks": ["is_dict"]},
        # # "testhtml_baseurl"      : {"default": "", "checks": ["is_str"]},
        # # "livehtml_baseurl"      : {"default": "", "checks": ["is_str"]},
        # "imgDestPath"           : {"checks": ["is_str"]},
        # "imgNameAllowRelative"  : {"default": True, "checks": ["is_bool"]},
        # "imgNameInsertInText"   : {"default": True, "checks": ["is_bool"]},
        # "imgPromptForName"      : {"default": False, "checks": ["is_bool"]},
        # "imgTypePrefs"          : {"default": ['png', 'jpg', 'jpeg'], "checks": ["is_list_of_oom_strings"]},
        # "imgNameFormat"         : {"default": "%Y-%m-%d--%H:%M:%Simage", "checks": ["is_str"]},
        # "roleDetails"           : {"default": [], "checks": ["is_list"]}
    }
}
