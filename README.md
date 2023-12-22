# LOG8415-FinalProject
LOG8415: Final Project Scaling Databases and Implementing Cloud Design Patterns

## How to set up
### 1. Install dependencies
```
pip install -r requirements.txt
```

### 1. Create the infrastructure
```
python src/deploy.py
```

### 2. Setup and Start the MySQL Servers
#### 2.1 Setup Standalone
Follow the steps in this tutorial [here](https://www.linode.com/docs/guides/install-mysql-on-ubuntu-14-04/)
#### 2.2 Setup Cluster
```
python src/mysql/generate_cluster_config_files.py
```
This will create the config files and the necessary directories in the master and data nodes.

Follow the steps from ***Initialize the Database*** step in this tutorial [here](https://stansantiago.wordpress.com/2012/01/04/installing-mysql-cluster-on-ec2/)

Once everything is setup you can now install sakila following this tutorial [here](https://dev.mysql.com/doc/sakila/en/sakila-installation.html)

#### 2.3 Start SQL Cluster
Now that you've configured and tested your MySQL cluster you can now use the command to start your MySQL cluster
```
python src/mysql/start_sql_cluster.py
```


### 3. Setup Proxy
To set up the proxy runs these commands
if first time running run this command to generate the key that's going to give the proxy ssh access to the MySQL nodes.
```
python src/proxy/generate_proxy_key.py
```
Then once your key is generated you can run this command to start the proxy.
```
python src/proxy/deploy_proxy.py
```

### 4. Setup Gatekeeper
To set up the Gatekeeper you can run these commands.
```
python src/gatekeeper/setup_gatekeeper_trusted_host_firewall.py
python src/gatekeeper/setup_gatekeeper.py
```
## Benchmark
- Connect to sql_bench instance
- Now follow this tutorial to benchmark your database [here](https://github.com/akopytov/sysbench)
### To benchmark the cluster
```
sysbench oltp_read_write --table_size=100000 --threads=32 --time=10 --max-requests=0 --mysql-host=<mysql-master-ip> --mysql-port=3306 --mysql-db=sakila --mysql-user=<your user> --mysql-password=<your password> prepare
sysbench oltp_read_write --table_size=100000 --threads=32 --time=10 --max-requests=0 --mysql-host=<mysql-master-ip> --mysql-port=3306 --mysql-db=sakila --mysql-user=<your user> --mysql-password=<your password> run
sysbench oltp_read_write --table_size=100000 --threads=32 --time=10 --max-requests=0 --mysql-host=<mysql-master-ip> --mysql-port=3306 --mysql-db=sakila --mysql-user=<your user> --mysql-password=<your password> cleanup
```
### To benchmark the standalone
```
sysbench oltp_read_write --table_size=100000 --threads=32 --time=10 --max-requests=0 --mysql-host=<mysql-standalone-ip> --mysql-port=3306 --mysql-db=sakila --mysql-user=<your user> --mysql-password=<your password> prepare
sysbench oltp_read_write --table_size=100000 --threads=32 --time=10 --max-requests=0 --mysql-host=<mysql-standalone-ip> --mysql-port=3306 --mysql-db=sakila --mysql-user=<your user> --mysql-password=<your password> run
sysbench oltp_read_write --table_size=100000 --threads=32 --time=10 --max-requests=0 --mysql-host=<mysql-standalone-ip> --mysql-port=3306 --mysql-db=sakila --mysql-user=<your user> --mysql-password=<your password> cleanup
```
## How to use
Once everything is setup you can send a request to the gatekeeper ingress using HTTP
```
http://<gatekeeper-ingress-public-dns-name>/
```
which should return you Hello World

Then you can get the mode by
```
GET http://<gatekeeper-ingress-public-dns-name>/mode
```

You can modify the mode by sending a PUT request with the body.
```
{
    "mode": "DIRECT_HIT" | "RANDOM" | "CUSTOMIZED"
}
```

```
PUT http://<gatekeeper-ingress-public-dns-name>/mode
```

To run queries you can send a POST 
```
POST http://<gatekeeper-ingress-public-dns-name>/query
```
with body
```
{
    "query": "<YOUR SQL QUERY>"
}
```

If your request doesn't have the proper body, your request will be refused by the GateKeeper. Also if you try to drop a database using the API, the Gatekeeper is going to refuse your request with status FORBIDDEN.
