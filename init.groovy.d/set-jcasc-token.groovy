def token = System.getenv('JCASC_RELOAD_TOKEN')
if (token) {
  println '[ciinabox] - setting jcasc reload token'
  System.setProperty('casc.reload.token', token)
}
