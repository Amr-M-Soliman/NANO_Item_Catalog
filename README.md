# Item Catalog

* It is a web application that provides a list of items within a variety of categories and integrate third party user registration and authentication.
* It implements a third-party authentication & authorization service ( `Google Accounts` and `Facebook Accounts`) instead of implementing its own authentication & authorization spec.
* Authenticated users have the ability to create, update, and delete their own categories and items.
* This project implements a `JSON endpoint` that serves the same information as displayed in the `HTML endpoints` for an arbitrary item in the catalog. 

## Getting Started ##
* You can clone the project by using git
```
    git clone https://github.com/Amr-M-Soliman/NANO_Item_Catalog.git
```
or *[download](https://github.com/Amr-M-Soliman/NANO_Item_Catalog/archive/master.zip)* this project via [GitHub](https://github.com) to your local machine.

### Requirements ###
* [Vagrant](https://www.vagrantup.com/downloads.html)
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)

### Installation of python ###
**Ubuntu**
```
    $ sudo apt-get update
    $ sudo apt-get install python3.6
```
**Windows**

Download the suitable installer from [downloads section](https://github.com/Amr-M-Soliman/Nano_Log_analysis.git) of the official Python website.

### Libraries ###
* **flask**:
    in cmd use `pip install flask`
* **redis**: 
    in cmd use `pip install redis`
* **requests**: *
    in cmd use `pip install requests`
* **json**: *
    in cmd use `pip install json`
* **flask_httpauth**: *
    in cmd use `pip install flask_httpauth`
* **sqlalchemy**: *
    in cmd use `pip install sqlalchemy`

 
### Installing VM ###

* Unzip the **VM configuration** and you will find a **vagrant** folder
* Use the **Terminal** to get into the **vagrant** folder from **VM configuration**
* run the following command
```sh
    $ vagrant up
```
* This will cause Vagrant to download the Linux operating system and install it.
* After it finished and after the shell prompt comes back, you can run this command
```sh
    $ vagrant ssh
```
* And this will let you login to the Linux VM. (Please do not shut down the terminal after the login)

### Setting up the enviroment ###
* Move the folder you downloaded from GitHub and put it into the vagrant folder
* use the following line to get into the vagrant VM folder
```sh
    $ cd /vagrant
```
* Use the command line to get in to the folder you just downloaded
* Then you can run this command to generate dummy data
```sh
    $ python lotsofcategories.py
```
* After it added items succesfully, you can run the following command
```sh
    $ python project.py
```
* After finish running project.py you can use your favorite browser to visit [this link](http://localhost:7000/)
