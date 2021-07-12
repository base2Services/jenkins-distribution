import jenkins.model.*
import hudson.model.*

def generatePassword(int length = 32) {
  String alphabet = (('A'..'N')+('P'..'Z')+('a'..'k')+('m'..'z')+('2'..'9')).join() 
  key = new Random().with {
    (1..length).collect { alphabet[ nextInt( alphabet.length() ) ] }.join()
  }
  return key
}

def bootstrap = new File("${System.getenv('JENKINS_HOME')}/bootstrap").exists()

def username = System.getenv('JENKINS_USERNAME')
if (!username && !bootstrap) {
  username = 'ciinabox'
}

def password = System.getenv('JENKINS_PASSWORD')
if (!password && !bootstrap) {
  password = generatePassword()
  println '*************************************************************'
  println '*************************************************************'
  println '*************************************************************\n'
  println 'An admin user has been created and a password generated. Please use the following password to login:\n'
  println "${password}\n"
  println 'Please change password when logged in.\n'
  println '*************************************************************'
  println '*************************************************************'
  println '*************************************************************'
}

user = hudson.model.User.get(username, false)

if (user == null && !bootstrap) {
  println "[ciinabox] - creating user"
  user = hudson.model.User.get(username)
  user.setFullName(username)
  
  println "[ciinabox] - setting email address"
  email = new hudson.tasks.Mailer.UserProperty('ciinabox@base2services.com')
  user.addProperty(email)
  
  println "[ciinabox] - setting password"
  password = hudson.security.HudsonPrivateSecurityRealm.Details.fromPlainPassword(password)
  user.addProperty(password)
  
  println "[ciinabox] - saving the user"
  user.save()
}

if (!bootstrap) {
  println("touch ${System.getenv('JENKINS_HOME')}/bootstrap".execute().text)
  println "[ciinabox] - created bootstrap file"
}