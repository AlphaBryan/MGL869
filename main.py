from collector import Collector
from dataCleaner import DataCleaner
from trainer import Trainer
import sys


class Main:
    collector = None
    dataCleaner = None
    trainer = None

    def init_collector(self, bugs_to_collect, vars_to_collect):
        self.collector = Collector(bugs_to_collect, vars_to_collect)

    def init_data_cleaner(self, clean_file):
        self.dataCleaner = DataCleaner(clean_file)

    def init_trainer(self, train_rfm, train_lr):
        self.trainer = Trainer(train_rfm, train_lr)

    def process(self):
        if self.collector != None:
            self.collector.collect()
        if self.dataCleaner != None:
            self.dataCleaner.clean_data('./files_vars.csv')
        if self.trainer != None:
            self.trainer.train_model()

     
if __name__ == "__main__":
    if len(sys.argv) < 1:
        exit()

    main = Main()
    args = sys.argv[1:]

    bugs_to_collect = '-cb' in args
    vars_to_collect = '-cv' in args
    clean_file = '-cf' in args
    train_rfm = '-rf' in args
    train_lr = '-lr' in args

    if bugs_to_collect or vars_to_collect:
        main.init_collector(bugs_to_collect, vars_to_collect)

    if clean_file:
        main.init_data_cleaner(clean_file)
    
    if train_rfm or train_lr:
        main.init_trainer(train_rfm, train_lr)

    main.process()