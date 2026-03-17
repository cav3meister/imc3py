import src.imc3py.wrapper as imc3

def test_1():
    f = imc3.IMC3File("tests\\data\\test_1c1.dat")
    assert f.header.dwMagic1 == 3478078285
    assert f.header.dwMagic2 == 466257884
    assert f.header.bVariant == 0
    assert f.header.bCs == 0
    assert f.header.bUnicode == 0
    assert f.header.bCompr == 0
    assert f.header.TimeZone == -1
    assert f.header.wSummertime == 0
    assert f.header.VersionMajor == 1
    assert f.header.VersionMinor == 1
    assert f.header.wCodePage == 1252
    assert f.header.wLanguage == 1031
    assert f.header.strFileProducer == 'Famos'
    assert f.header.strFileComment == ''
    assert f.header.dwCountGroups == 0
    assert f.header.dwCountNamedChannels == 1
    assert f.header.dwCountIndexChannels == 1
    assert f.header.dwCountTextVars == 0
    assert f.header.dwCountSingleValues == 0
    
def test_2():
    f = imc3.IMC3File("tests\\data\\test_1c2.dat")
    assert f.header.dwMagic1 == 2513682580
    assert f.header.dwMagic2 == 701942200
    assert f.header.bVariant == 0
    assert f.header.bCs == 0
    assert f.header.bUnicode == 0
    assert f.header.bCompr == 0
    assert f.header.TimeZone == -1
    assert f.header.wSummertime == 0
    assert f.header.VersionMajor == 1
    assert f.header.VersionMinor == 2
    assert f.header.wCodePage == 1252
    assert f.header.wLanguage == 1031
    assert f.header.strFileProducer == 'Famos'
    assert f.header.strFileComment == ''
    assert f.header.dwCountGroups == 0
    assert f.header.dwCountNamedChannels == 1
    assert f.header.dwCountIndexChannels == 1
    assert f.header.dwCountTextVars == 0
    assert f.header.dwCountSingleValues == 0
    
def test_3():
    f = imc3.IMC3File("tests\\data\\test_1c3.dat")
    print(f.header)
    assert f.header.dwMagic1 == 2061303317
    assert f.header.dwMagic2 == 701942281
    assert f.header.bVariant == 0
    assert f.header.bCs == 0
    assert f.header.bUnicode == 0
    assert f.header.bCompr == 0
    assert f.header.TimeZone == -1
    assert f.header.wSummertime == 0
    assert f.header.VersionMajor == 1
    assert f.header.VersionMinor == 2
    assert f.header.wCodePage == 1252
    assert f.header.wLanguage == 1031
    assert f.header.strFileProducer == 'Famos'
    assert f.header.strFileComment == ''
    assert f.header.dwCountGroups == 0
    assert f.header.dwCountNamedChannels == 1
    assert f.header.dwCountIndexChannels == 1
    assert f.header.dwCountTextVars == 0
    assert f.header.dwCountSingleValues == 0
    
def test_4():
    f = imc3.IMC3File("tests\\data\\test_1g_2c1_1v.dat")
    assert f.header.dwMagic1 == 2421102770
    assert f.header.dwMagic2 == 701941632
    assert f.header.bVariant == 0
    assert f.header.bCs == 0
    assert f.header.bUnicode == 0
    assert f.header.bCompr == 0
    assert f.header.TimeZone == -1
    assert f.header.wSummertime == 0
    assert f.header.VersionMajor == 1
    assert f.header.VersionMinor == 2
    assert f.header.wCodePage == 1252
    assert f.header.wLanguage == 1031
    assert f.header.strFileProducer == 'Famos'
    assert f.header.strFileComment == ''
    assert f.header.dwCountGroups == 1
    assert f.header.dwCountNamedChannels == 2
    assert f.header.dwCountIndexChannels == 2
    assert f.header.dwCountTextVars == 0
    assert f.header.dwCountSingleValues == 1
    
def test_5():
    f = imc3.IMC3File("tests\\data\\test_3g_2c1_2v.dat")
    print(f.header)
    assert f.header.dwMagic1 == 4024201572
    assert f.header.dwMagic2 == 702205699
    assert f.header.bVariant == 0
    assert f.header.bCs == 0
    assert f.header.bUnicode == 0
    assert f.header.bCompr == 0
    assert f.header.TimeZone == -1
    assert f.header.wSummertime == 0
    assert f.header.VersionMajor == 1
    assert f.header.VersionMinor == 2
    assert f.header.wCodePage == 1252
    assert f.header.wLanguage == 1031
    assert f.header.strFileProducer == 'Famos'
    assert f.header.strFileComment == ''
    assert f.header.dwCountGroups == 3
    assert f.header.dwCountNamedChannels == 2
    assert f.header.dwCountIndexChannels == 2
    assert f.header.dwCountTextVars == 0
    assert f.header.dwCountSingleValues == 2
      
def test_6():
    f = imc3.IMC3File("tests\\data\\test_1t_1ta.dat")
    print(f.header)
    assert f.header.dwMagic1 == 1505619818
    assert f.header.dwMagic2 == 701942343
    assert f.header.bVariant == 0
    assert f.header.bCs == 0
    assert f.header.bUnicode == 0
    assert f.header.bCompr == 0
    assert f.header.TimeZone == -1
    assert f.header.wSummertime == 0
    assert f.header.VersionMajor == 1
    assert f.header.VersionMinor == 2
    assert f.header.wCodePage == 1252
    assert f.header.wLanguage == 1031
    assert f.header.strFileProducer == 'Famos'
    assert f.header.strFileComment == ''
    assert f.header.dwCountGroups == 0
    assert f.header.dwCountNamedChannels == 0
    assert f.header.dwCountIndexChannels == 0
    assert f.header.dwCountTextVars == 2
    assert f.header.dwCountSingleValues == 0