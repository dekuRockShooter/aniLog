from ui import UI
import shared
import settings

shared.UIRegistry.create(settings.key_map)
ui = shared.UIRegistry.get()
ui.create()
ui.get_key()
shared.UIRegistry.destroy()
