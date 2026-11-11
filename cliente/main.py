import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from clientemodbus import ClienteMODBUS

Window.size = (480, 620)

KV = '''
MDBoxLayout:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(12)

    MDLabel:
        text: "Cliente Modbus TCP - KivyMD"
        halign: "center"
        font_style: "H6"
        size_hint_y: None
        height: dp(40)

    # --- (IP, Porta e Botão Conectar) ---
    MDBoxLayout:
        orientation: 'horizontal'
        spacing: dp(10)
        size_hint_y: None
        height: dp(60)

        MDTextField:
            id: ip_field
            text: "localhost"
            hint_text: "IP do Servidor"
            size_hint_x: 0.5

        MDTextField:
            id: port_field
            text: "502"
            hint_text: "Porta"
            input_filter: "int"
            size_hint_x: 0.25

        MDRaisedButton:
            id: btn_conectar
            text: "Conectar"
            size_hint_x: 0.25
            pos_hint: {"center_y": 0.5}
            on_release: app.alternar_conexao()

    MDLabel:
        id: conn_status_label
        text: "Conexão: Desconectado"
        halign: "center"
        theme_text_color: "Secondary"
        size_hint_y: None
        height: dp(30)

    Widget:
'''


class ModbusGUIApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        # Instancia o cliente sem forçar conexão automática no build()
        self.modbus = ClienteMODBUS()
        return Builder.load_string(KV)

    def alternar_conexao(self):
        """Lê IP e Porta digitados na interface e conecta ou desconecta."""
        if not self.modbus.conectado:
            ip = self.root.ids.ip_field.text.strip() or "localhost"
            porta_str = self.root.ids.port_field.text.strip() or "502"

            self.modbus.configurar_conexao(ip, int(porta_str))
            if self.modbus.conectar():
                self.root.ids.conn_status_label.text = f"Conexão: Conectado em {ip}:{porta_str}"
                self.root.ids.btn_conectar.text = "Desconectar"
            else:
                self.root.ids.conn_status_label.text = f"Conexão: Falha ao conectar em {ip}:{porta_str}"
        else:
            self.modbus.desconectar()
            self.root.ids.conn_status_label.text = "Conexão: Desconectado"
            self.root.ids.btn_conectar.text = "Conectar"


if __name__ == '__main__':
    ModbusGUIApp().run()