import ui
import shared
import settings.keys

ui.UIRegistry.create(settings.keys.key_map)
user_interface = ui.UIRegistry.get()
user_interface.create()
user_interface.get_key()
ui.UIRegistry.destroy()
