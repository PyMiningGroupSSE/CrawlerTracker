FROM python:3.7.1-slim

VOLUME [ "/configs" ]

RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak \
    && echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian/ stretch main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-updates main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian/ stretch-backports main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian-security stretch/updates main contrib non-free" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y --no-install-recommends wget \
    && pip config set global.index-url "https://pypi.tuna.tsinghua.edu.cn/simple" \
    && pip install requests pymongo flask configobj \
    && wget -O tracker.tar.gz "https://github.com/PyMiningGroupSSE/CrawlerTracker/archive/master.tar.gz" \
    && tar -xzf tracker.tar.gz && mv CrawlerTracker-master crawler-tracker \
    && rm tracker.tar.gz \
    && apt-get remove --purge -y wget \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 12345
EXPOSE 25316
WORKDIR /crawler-tracker
CMD chown -R root:root /configs && sh DockerInit.sh && python tracker.py