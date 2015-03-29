import utils as ut
import yaml
from copy import deepcopy
from nose import *

class TestDictMerge:


    def test_dict_merge(self):
        self.dict_list_1 = [1, 2, 3]
        self.dict_list_2 = [3, 4, "potato"]
        self.dict_dict_1 = {"a": "potato",
                            "b": "potato",
                            "c": "squash",
                            "potato": 37}
        self.dict_dict_2 = {"a": "blueberry",
                            "b": "potato"}


        assert ut.recursive_dict_merge(deepcopy(self.dict_list_1), self.dict_list_2) == [1, 2, 3, 3, 4, "potato"]
        assert ut.recursive_dict_merge(deepcopy(self.dict_dict_1), self.dict_dict_2) == {"a": "potato",
                                                                                         "b": "potato",
                                                                                         "c": "squash",
                                                                                         "potato": 37}
        assert ut.recursive_dict_merge(deepcopy(self.dict_dict_2), self.dict_dict_1) == {"a": "blueberry",
                                                                                         "b": "potato",
                                                                                         "c": "squash",
                                                                                         "potato": 37}

        

