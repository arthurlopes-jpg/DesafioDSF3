from servidormodbus import ServidorMODBUS

if __name__ == '__main__':
    s = ServidorMODBUS('localhost', 502)
    s.run()