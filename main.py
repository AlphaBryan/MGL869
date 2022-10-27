from collector import Collector
from dataClean import DataClean
import sys


class Main:
    collector = None
    dataClean = None

    def init_collector(self, bugs_to_collect, vars_to_collect):
        self.collector = Collector(bugs_to_collect, vars_to_collect)

    def init_clean_file(self, clean_file):
        self.dataClean = DataClean(clean_file)

    def process(self):
        if self.collector != None:
            self.collector.collect()
        if self.dataClean != None:
            self.dataClean.clean_data('./files_vars.csv')

     
if __name__ == "__main__":
    if len(sys.argv) < 1:
        exit()

    main = Main()
    args = sys.argv[1:]

    bugs_to_collect = '-cb' in args
    vars_to_collect = '-cv' in args
    clean_file = '-cf' in args

    if bugs_to_collect or vars_to_collect:
        main.init_collector(bugs_to_collect, vars_to_collect)

    if clean_file:
        main.init_clean_file(clean_file)

    main.process()