echo "📦 Setting up nitro instance"

sudo amazon-linux-extras install aws-nitro-enclaves-cli -y
sudo yum install aws-nitro-enclaves-cli-devel -y 

sudo usermod -aG ne ec2-user
sudo usermod -aG docker ec2-user
sudo systemctl enable nitro-enclaves-allocator.service
sudo systemctl start nitro-enclaves-allocator.service
nitro-cli --version
sudo yum install -y make


echo 'install gvproxy'
sudo yum install golang
go install github.com/containers/gvisor-tap-vsock/cmd/gvproxy@latest
sudo echo 'export PATH=$PATH:/home/ec2-user/gvisor-tap-vsock/bin' >> ~/.bashrc
sudo echo 'export PATH=$PATH:/home/ec2-user/gvisor-tap-vsock/bin' >> sudo /etc/environment
source ~/.bashrc
source /etc/environment

echo "✅ Setup done, reboot with 'sudo reboot'"