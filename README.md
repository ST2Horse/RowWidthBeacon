# RowWidthBeacon

RowWidthBeacon 是一个本地 CSV 检查工具：根据第一条记录的表头，查找列数不一致的记录，统计每列空值，并提示空表头和重复表头。适合在导入报名表、问卷导出文件或实验记录之前做一次检查。程序不会改写原文件，也不访问网络。

版本 0.1.0；需要 Python 3.10 或以上，仅使用标准库。窗口版还需要 Tkinter。

## 下载与运行

- 项目主页：https://github.com/ST2Horse/RowWidthBeacon
- ZIP 下载：https://github.com/ST2Horse/RowWidthBeacon/archive/refs/heads/main.zip

下载后完整解压。Windows 用户可双击 `打开工具.cmd`，选择 CSV 文件后点击“开始检查”。该启动方式要求 `python` 命令可用，并已安装 Tkinter。窗口默认以逗号分隔，可修改编码和空值提醒数量；其他分隔符请用命令行。

在工具目录中打开终端，运行：

```powershell
python rowwidthbeacon.py demo/sample.csv
python rowwidthbeacon.py demo/sample.csv --rowwidthbeacon-blank-limit 2
python rowwidthbeacon.py demo/sample.csv --json
python rowwidthbeacon.py --gui
```

## 一个实际例子

附带的 `demo/sample.csv` 是虚构的演示数据：

```csv
name,email,city
Alice,alice@example.invalid,北京
Bob,,上海
Carol, ,深圳
Dave,dave@example.invalid
```

运行 `python rowwidthbeacon.py demo/sample.csv --rowwidthbeacon-blank-limit 2` 得到：

```text
RowWidthBeacon 0.1.0
Expected columns: 3
Data records: 4
Matching-width records: 3
Width mismatches: 1
Blank limit: 2
Blank counts use matching-width records only.
Column 1 "name": blank=0 OK
Column 2 "email": blank=2 ALERT
Column 3 "city": blank=0 OK
Record 5, lines 5-5: actual columns=2
```

这里有 4 条数据记录，其中 3 条列数正确；第 5 条 CSV 记录（包含表头计数）只有 2 列。email 列有两个空值，因此达到数量 2，显示 ALERT。示例中的邮箱只用于演示，不是真实联系地址。

## 特有参数怎么用

`--rowwidthbeacon-blank-limit N` 指定同一列空值数量达到多少时提醒，默认 1，必须为至少 1 的整数。空字符串和只包含空白字符的字段都算空值。

**空值统计只包含列数与表头一致的数据记录。** 少列记录不会被自动补齐、加入空值数量。这个参数只调整空值提醒，不改变列数检查结果，也不会删除或补写数据。上例把参数改为 3 后，email 的空值数量仍为 2，但不再触发空值提醒；少列记录仍然报告。

## 参数

| 参数 | 用途 |
| --- | --- |
| `file` | 输入 CSV 文件，第一条记录必须为非空表头 |
| `--rowwidthbeacon-blank-limit N` | 同一列空值数量达到 N 时提醒，默认 1 |
| `--encoding NAME` | 输入编码，默认 `utf-8-sig`，接受有或没有 BOM 的 UTF-8 |
| `--delimiter CHAR` | 单字符分隔符，默认逗号；例如 `--delimiter ";"` |
| `--max-details N` | 最多展示 N 条列数异常的明细，默认 100；总数仍完整统计 |
| `--json` | 在终端输出 JSON 报告 |
| `--gui` | 打开窗口；窗口使用逗号分隔和 100 条明细上限 |
| `--version` | 显示版本 |

## 规则与限制

- 使用 Python `csv.reader` 解析引号内的逗号和换行，不是把每个物理行直接按逗号拆分。记录号从表头开始计为 1，明细另给出实际行号范围。
- 空白物理行会作为 0 列的记录报告；文件末尾单个换行不会额外产生记录。
- 重复表头按原文完全相同判断，区分大小写和首尾空白；空表头按去除首尾空白后是否为空判断。不自动修改表头。
- 只检查结构和空值，不核对邮箱格式、数值范围、内容真假或跨行重复；不读取 Excel 工作簿。
- 列数正常不代表数据完全正确。空值也可能符合业务要求，由使用者判断。
- 不自动猜编码或分隔符。语法无法解析、编码错误、空文件或文件不可读时退出并报告错误，不把部分结果当成完整报告。
- 使用标准库默认的 CSV 字段长度限制；单字段过长时会报解析错误。
- 按记录读取，保存每列计数和有限明细。异常记录的字段内容不写入报告，但报告包含原表头。
- 命令行退出码：0 表示检查完成且未发现当前规则下的问题；1 表示检查完成并有提醒；2 表示输入或参数错误。演示文件返回 1 是预期结果。

## 测试

```powershell
python -m unittest discover -s tests -v
```

覆盖中文与 BOM、引号内换行、记录位置、空表头和重复表头、空值数量边界、明细上限、分隔符、错误输入与退出码，并检查输入内容未改变。
