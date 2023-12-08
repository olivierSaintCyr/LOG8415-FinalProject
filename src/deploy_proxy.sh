
python src/proxy/generate_config.py
scp -i "final_project_gen_key.pem" src/proxy/app.py src/proxy/requirements.txt src/proxy/config.json src/proxy/proxy_key.pem ubuntu@ec2-52-87-207-207.compute-1.amazonaws.com:/home/ubuntu
ssh -i "final_project_gen_key.pem" ubuntu@ec2-52-87-207-207.compute-1.amazonaws.com 'sudo NEEDRESTART_MODE=a apt-get update -y'
ssh -i "final_project_gen_key.pem" ubuntu@ec2-52-87-207-207.compute-1.amazonaws.com 'sudo NEEDRESTART_MODE=a apt-get install python3-pip -y'
ssh -i "final_project_gen_key.pem" ubuntu@ec2-52-87-207-207.compute-1.amazonaws.com 'sudo pip3 install -r requirements.txt'
ssh -i "final_project_gen_key.pem" ubuntu@ec2-52-87-207-207.compute-1.amazonaws.com 'pkill -f python'
ssh -i "final_project_gen_key.pem" ubuntu@ec2-52-87-207-207.compute-1.amazonaws.com 'nohup sudo python3 app.py &'
