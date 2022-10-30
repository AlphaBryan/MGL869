from collector import Collector
from dataCleaner import DataCleaner
from trainer import Trainer
from validator import Validator
import sys


class Main:
    collector = None
    dataCleaner = None
    trainer = None
    validator = None

    def init_collector(self, bugs_to_collect, vars_to_collect):
        self.collector = Collector(bugs_to_collect, vars_to_collect)

    def init_data_cleaner(self, clean_file):
        self.dataCleaner = DataCleaner(clean_file)

    def init_trainer(self, train_rf, train_lr):
        self.trainer = Trainer(train_rf, train_lr)

    def init_validator(self, validate_rf, validate_lr):
        self.validator = Validator(validate_rf, validate_lr)

    def process(self):
        if self.collector != None:
            self.collector.collect()
        if self.dataCleaner != None:
            self.dataCleaner.clean_data('./files_vars.csv')
        if self.trainer != None:
            self.trainer.train_model()
        if self.validator != None:
            self.validator.validate_model()

     
if __name__ == "__main__":
    if len(sys.argv) < 1:
        exit()

    main = Main()
    args = sys.argv[1:]

    bugs_to_collect = '-cb' in args
    vars_to_collect = '-cv' in args
    clean_file = '-cf' in args
    train_rf = '-rf' in args
    train_lr = '-lr' in args
    validate_rf = '-vrf' in args
    validate_lr = '-vlr' in args

    if bugs_to_collect or vars_to_collect:
        main.init_collector(bugs_to_collect, vars_to_collect)

    if clean_file:
        main.init_data_cleaner(clean_file)
    
    if train_rf or train_lr:
        main.init_trainer(train_rf, train_lr)

    if validate_rf or validate_lr:
        main.init_validator(validate_rf, validate_lr)

    main.process()