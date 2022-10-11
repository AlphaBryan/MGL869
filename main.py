from collector import Collector
import sys


class Main:
    collector = None

    def init_collector(self, bugs_to_collect, vars_to_collect):
        self.collector = Collector(bugs_to_collect, vars_to_collect)

    def process(self):
        if self.collector != None:
            self.collector.collect()

     
if __name__ == "__main__":
    if len(sys.argv) < 1:
        exit()

    main = Main()
    args = sys.argv[1:]

    bugs_to_collect = '-cb' in args
    vars_to_collect = '-cv' in args

    if bugs_to_collect or vars_to_collect:
        main.init_collector(bugs_to_collect, vars_to_collect)

    main.process()