#!/usr/bin bash

OS=linux
ARCH=amd64

### setup

mkdir ~/tmp/
cd ~/tmp/ || exit

### primary dependencies

sudo dnf install -y git

### applications

# [install Google Chrome](https://www.if-not-true-then-false.com/2010/install-google-chrome-with-yum-on-fedora-red-hat-rhel/)
sudo dnf install -y fedora-workstation-repositories
sudo dnf config-manager --set-enabled google-chrome
sudo dnf install -y google-chrome-stable

### languages

# [install Golang](https://golang.org/dl/)
GO_VERSION="1.11.1"
GO_ARCHIVE="go$GO_VERSION.$OS-$ARCH.tar.gz"

wget "https://dl.google.com/go/$GO_ARCHIVE"
sudo tar -C /usr/local -xzf "$GO_ARCHIVE"

# [make go workspace](https://golang.org/doc/code.html#Workspaces)
mkdir -p ~/code/go

# [install nodejs using nvm](https://github.com/creationix/nvm#install-script)
#   must
#     nvm install <version>
#     nvm use <version>
#   before node or npm are available
NVM_VERSION="0.33.11"
curl -o- "https://raw.githubusercontent.com/creationix/nvm/v$NVM_VERSION/install.sh" | bash

### infrastructural tools

# [install Docker](https://docs.docker.com/install/linux/docker-ce/fedora/#install-docker-ce)
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce

# [install awscli](https://docs.aws.amazon.com/cli/latest/userguide/awscli-install-bundle.html)
sudo dnf install -y python
curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
unzip awscli-bundle.zip
sudo ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws

# [install terraform](https://www.terraform.io/downloads.html)
TERRAFORM_VERSION="0.11.10"
TERRAFORM_ARCHIVE="$TERRAFORM_VERSION/terraform_${TERRAFORM_VERSION}_${OS}_${ARCH}.zip"

wget "https://releases.hashicorp.com/terraform/$TERRAFORM_ARCHIVE"
unzip "$TERRAFORM_ARCHIVE"
sudo mv ./terraform /usr/local/bin

# [install virtualbox](https://medium.com/@Joachim8675309/vagrant-and-friends-on-fedora-28-37b8cbc47e47)

  # download virtualbox.repo file for yum
sudo wget -P /etc/yum.repos.d/ https://download.virtualbox.org/virtualbox/rpm/fedora/virtualbox.repo
sudo dnf update -y
  # install kernel development packages
sudo dnf install -y \
  binutils \
  gcc \
  make \
  patch \
  libgomp \
  glibc-headers \
  glibc-devel \
  kernel-headers \
  kernel-devel \
  dkms
  # install/setup VirtualBox 5.2.x
sudo dnf install -y VirtualBox-5.2
sudo /usr/lib/virtualbox/vboxdrv.sh setup
  # test version
sudo vboxmanage --version
  # enable current user
sudo usermod -a -G vboxusers "${USER}"

# [install vagrant](https://medium.com/@Joachim8675309/vagrant-and-friends-on-fedora-28-37b8cbc47e47)
VAGRANT_VERSION="2.2.0"
VAGRANT_ARCHIVE="vagrant_${VAGRANT_VERSION}_${OS}_${ARCH}.zip"
wget "https://releases.hashicorp.com/vagrant/$VAGRANT_VERSION/$VAGRANT_ARCHIVE"
unzip "$VAGRANT_ARCHIVE"
mv ./vagrant /usr/local/bin

### code editor, shell

# [install janus distribution of vim](https://github.com/carlhuda/janus)
sudo dnf install -y ack
sudo dnf install -y ctags
sudo dnf install -y gvim
sudo dnf install -y vim
sudo dnf install -y ruby
sudo gem install rake
curl -L https://bit.ly/janus-bootstrap | bash

# install tmux
sudo dnf install -y tmux

# install [zsh with oh-my-zsh framework](https://github.com/robbyrussell/oh-my-zsh)
sudo dnf install -y zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"

# [install the_silver_searcher](https://github.com/ggreer/the_silver_searcher)
sudo dnf install -y the_silver_searcher

### nifty tools

sudo dnf install -y feh # image displayer
sudo dnf install -y xclip # command line clipboard grabber

### download dotfiles

git clone https://github.com/calebgregory/tools ~/tools

cd ~/tools/dotfiles || exit
bash ./bootstrap-util/symlink-dotfiles.sh

bash ./bootstrap-util/install-vim-plugins.sh

### GUI

gsettings set org.gnome.desktop.background picture-uri ~/tools/dotfiles/assets/sea_drawing.jpg
gsettings set org.gnome.desktop.screensaver picture-uri ~/tools/dotfiles/assets/sea_drawing.jpg

### clean up

rm -rf ~/tmp/
