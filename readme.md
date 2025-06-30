# IGV Browser



> authors: chengchaoze@gmail.com
>
> date: 20220310


- https://igv.org/doc/webapp/#Hosting/


## Usage

1. chrome brower 打开网址 http://10.81.112.94:50001

2. 加载完成 iGV web 页面，选择基因组版本（hg19, hg38, mm10），默认展示 hg19

3. 打开服务器端 bam 文件

   - 运行脚本 link4iGVweb.py 链接 bam 文件到特定目录，复制脚本输出的 web 服务器路径

     > ```shell
     > python link4iGVweb.py $BamFile
     >
     > # OR
     > python link4iGVweb.py $ProjectDir
     > ```

   - 或手动连接 bam/bai 文件到特定路径，

2. 在 iGV web 页面，操作 web => Tracks => URL... => 复制粘贴对应的 bam/bai 链接即可

> 和本地 iGV 客户端一致，iGV web 同时支持本地 bam/bed 文件上传查看



##Build

1. download

   ```shell
   wget -c https://github.com/igvteam/igv-webapp/archive/refs/tags/v1.9.0.zip
   wget -c https://igv.org/app-archive/igv-webapp.2.2.7.zip
   ```

2. 修改 igv-webapp 程序中远程路径

   - 网页显示 css/js 等文件下载到本地，修改 index.html
   - igv-webapp 配置文件修改，基因组相关文件下载到本地
   - 创建本地文件夹用于 bam 文件储存

3. 构建本地 docker image

   ```shell
   COPYFILE_DISABLE=1 tar zcf igv-webapp.1.9.0.tar.gz igv-webapp.1.9.0

   docker build -t igv-webapp .
   ```

4. 启动 iGV web 服务

   ```shell
   docker run -it -p 50001:80 \
   	-v $LocalResouces:/opt/igv-webapp.1.9.0/resources \
   	-v /glusterfs/home/:/glusterfs/home/ \
   	-v /titan3:/titan3 \
     igv-webapp
   ```

   注意事项：

   - 仅支持 /glusterfs/home/ 以及 /titan3 两个目录的 bam 文件进行 IGV web方式查看
   - 设置 **$LocalResouces/data** 路径权限为 777，便于使用该目录进行 bam 链接
   - 目前 docker iamge 运行暂不能后台，需要交互方式进入，手动在后台常驻

5. 服务器部署

   本地数据库文件、bam 储存在目录 **/titan3/igv-webapp.1.9.0**


6. nginx 

vi /etc/nginx/sites-available/default

server {
    listen  8889;
    listen [::]:8889;

    location / {
        root   /path/to/service/igv_web/igv-webapp;
        index  index.html index.htm;
    }
}

