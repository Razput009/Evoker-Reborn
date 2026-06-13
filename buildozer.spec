[app]
title = Evoker Reborn
package.name = evokerreborn
package.domain = org.evokerreborn

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,pygame

orientation = portrait
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.permissions = 
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
