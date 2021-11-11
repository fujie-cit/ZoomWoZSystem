import csv


class CSVProcessing:
    def __init__(self):
        pass

    def read(self, path):
        f = open(path, 'r')
        reader = csv.reader(f)
        data = []
        for row in reader:
            data.append(row)
        f.close()
        return data

    def write(self, path, data):
        f = open(path, 'a', encoding="utf_8_sig")
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(data)
        f.close()

    def to_csv(self, df, path):
        df.to_csv(path, encoding='utf-8-sig', index=False)
