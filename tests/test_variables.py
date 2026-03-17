import src.imc3py.wrapper as imc3

def test_isVariable1():
    f = imc3.IMC3File("tests\\data\\test_1t_1ta.dat")
    assert f.isVariable("MyTextArray")
    assert not f.isVariable("mytextarray")
    assert not f.isVariable("MyTextaRray")
    assert f.isVariable("MyText")
    assert not f.isVariable("MyText_")
    assert not f.isVariable("MyTex")
    assert not f.isVariable("mytext")
    
def test_isVariable2():
    f = imc3.IMC3File("tests\\data\\test_3g_2c1_2v.dat")
    print(f.list_variables())
    assert f.isVariable("ABC:xd")
    assert not f.isVariable("Xd")
    assert not f.isVariable("xD")
    assert f.isVariable("Groupname:MySingleValue")
    assert not f.isVariable("")
    assert not f.isVariable("MyTex")
    assert not f.isVariable("mytext")
    assert f.isVariable("Groupname:OffsetRamp")
    assert not f.isVariable("offsetRamp")
    assert not f.isVariable(":OffsetRamp")
    assert not f.isVariable("groupname:OffsetRamp")
    
def test_singleValues1():
    f = imc3.IMC3File("tests\\data\\test_3g_2c1_2v.dat")
    assert f.get_variable_by_name("ABC:xd").group_id == 1
    assert f.get_variable_by_name("ABC:xd").dTime == 1458123104
    assert f.get_variable_by_name("ABC:xd").value == 0.001
    assert f.get_variable_by_name("ABC:xd").unit == ''
    assert f.get_variable_by_name("Groupname:MySingleValue").group_id == 2
    assert f.get_variable_by_name("Groupname:MySingleValue").dTime == 1226581385
    assert f.get_variable_by_name("Groupname:MySingleValue").value == 1.0
    assert f.get_variable_by_name("Groupname:MySingleValue").unit == 'V'