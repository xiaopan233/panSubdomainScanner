# panSubdomainScanner
子域名收集和整理脚本（python3）

本脚本基于oneforall收集到的子域名的基础上，再次探测和扫描、网页截图，使用html的形式展示

使用方式：
sudo python3 panSubdomainScanner.py xxx.csv &#91;port&#93;

其中。xxx.csv为oneforall收集得到的csv，port可选。为要扫描的端口，脚本默认扫描了80和443，如果要新增端口的话就可以写上去（不需要再写80和443），多个端口用英文逗号分开。

本脚本使用了：
nmap作为存活探测以及端口探测
requests验证http和https，以及抓取header
selenium进行网页截图

需要安装的库：
pip3 install selenium
pip3 install requests

nmap的话我附带上来了，应该不用再装。
