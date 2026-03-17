import src.imc3py.wrapper as imc3

def test_full_file():
    f = imc3.IMC3File("tests\\data\\test_all.dat")
    assert f.isVariable("Auswertung:filter_char")
    assert not f.isVariable("Kanal_1:filter_char")
    assert not f.isVariable("filter_char")
    assert f.isVariable("Kanal_1:sprung_1_1")
    assert f.isVariable("Kanal_1:sprung_1_5")
    assert not f.isVariable("Kanal_1:sprung_1_6")
    assert f.get_variable_by_name("Auswertung:filter_grenzfreq").value == 100
    assert f.get_variable_by_name("Auswertung:filter_cutIn").value == 0.5
    assert f.get_variable_by_name("Kanal_1:name").value == 'pZu'
    assert f.get_variable_by_name("Kanal_1:einheit").value == 'bar'
    assert f.get_variable_by_name("Sprung_1:kanal_1").value == 'Kanal_3:kanal_filt'
    assert f.get_variable_by_name("Sprung_1:s_prozentgrenze").value == 66
    assert f.get_variable_by_name("Sprung_3:kanal_2").value == 'Kanal_2:kanal_filt'
    
    dfr = f.channel_as_df("Kanal_1:kanal_roh")
    assert len(dfr.index) == 416905
    assert round(dfr['y'].iloc[0], 6) == 21.947023
    assert round(dfr['y'].iloc[1], 6) == 21.974400
    assert round(dfr['y'].iloc[2], 6) == 21.986567
    assert round(dfr['y'].iloc[-3], 6) == 20.039777
    assert round(dfr['y'].iloc[-2], 6) == 20.033693
    assert round(dfr['y'].iloc[-1], 6) == 0
    dff = f.channel_as_df("Kanal_1:kanal_filt")
    assert len(dff.index) == 396905
    assert round(dff['y'].iloc[0], 6) == 8.129579
    assert round(dff['y'].iloc[1], 6) == 8.136665
    assert round(dff['y'].iloc[2], 6) == 8.143761
    assert round(dff['y'].iloc[-3], 6) == 21.930725
    assert round(dff['y'].iloc[-2], 6) == 21.931189
    assert round(dff['y'].iloc[-1], 6) == 21.931654
    dfs = f.channel_as_df("Kanal_1:sprung_1_3")
    assert len(dfs.index) == 45784
    assert round(dfs['y'].iloc[0], 6) == 21.906393
    assert round(dfs['y'].iloc[1], 6) == 21.906469
    assert round(dfs['y'].iloc[2], 6) == 21.906570
    assert round(dfs['y'].iloc[-3], 6) == 21.903397
    assert round(dfs['y'].iloc[-2], 6) == 21.902319
    assert round(dfs['y'].iloc[-1], 6) == 21.901224