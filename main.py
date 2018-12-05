from configure import Configure

c = Configure("./config.ini")
# c.write('global', 'test', 'a')

# print(c.read('global', 'test2', 'def'))
c.read_float('glo', 'test6', 4)

