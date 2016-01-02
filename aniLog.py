from ui import UI
import shared
import settings.keys

shared.UIRegistry.create(settings.keys.key_map)
ui = shared.UIRegistry.get()
ui.create()
ui.get_key()
shared.UIRegistry.destroy()
