from cliente.clientemodbus import ClienteMODBUS

if __name__ == '__main__':
    c = ClienteMODBUS('localhost', 502)
    c.atendimento()