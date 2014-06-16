from taiga import sqlmeta

def test_create_permaname():
  okay_except_a_few = lambda x: (x in ["a", "a-1", "a-2"])
  
  # basics work
  assert sqlmeta.create_permaname("Phil's data", okay_except_a_few) == "phils-data"
  
  # make sure multiple non-alphanumerics get collapsed
  assert sqlmeta.create_permaname("Phil's !#!@#!@ data", okay_except_a_few) == "phils-data"
  
  # make sure that we create a unique suffix
  assert sqlmeta.create_permaname("a", okay_except_a_few) == "a-3"
  