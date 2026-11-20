import os, unittest
from unittest.mock import patch
import deploy

CONFIG={
 'HOSTINGER_HOST':'example.com','HOSTINGER_USER':'u123','HOSTINGER_PORT':'65002',
 'HOSTINGER_SSH_KEY':'TEST ONLY','HOSTINGER_KNOWN_HOSTS':'TEST ONLY',
 'HOSTINGER_TARGET_DIR':'/home/u123/domains/bleenky.com/public_html/demos',
 'DEMO_BASE_URL':'https://bleenky.com/demos/',
 'GITHUB_RUN_ID':'123','GITHUB_RUN_ATTEMPT':'1'
}
class DeploymentTests(unittest.TestCase):
 def test_missing_credentials_fail_closed(self):
  with self.assertRaisesRegex(ValueError,'Missing settings'): deploy.settings({})
 def test_target_rejects_unsafe_or_wrong_account_paths(self):
  for path in ['/', '/home/u123', '/home/u123/domains/bleenky.com/public_html/../other','/home/other/domains/bleenky.com/public_html','/tmp/demo;echo bad']:
   with self.subTest(path=path), self.assertRaises(ValueError): deploy.settings(dict(CONFIG,HOSTINGER_TARGET_DIR=path))
 def test_requires_https(self):
  with self.assertRaises(ValueError): deploy.settings(dict(CONFIG,DEMO_BASE_URL='http://example.com'))
 def test_dry_run_never_checks_or_changes_live_site(self):
  with patch.dict(os.environ,dict(CONFIG,DRY_RUN='true'),clear=True),patch('deploy.subprocess.run') as run,patch('deploy.urlopen') as web:
   deploy.main()
   self.assertEqual(run.call_count,2)
   args=run.call_args_list[-1].args[0]
   self.assertIn('--dry-run',args);self.assertNotIn('--delete',args)
   self.assertIn('-rzp',args)  # Apply readable permissions even with Hostinger's restrictive umask.
   self.assertIn('--chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r',args)
   self.assertIn('StrictHostKeyChecking=yes',run.call_args_list[0].args[0])
   self.assertIn('UserKnownHostsFile=', ' '.join(run.call_args_list[0].args[0]))
   web.assert_not_called()
 def test_failed_ssh_does_not_transfer(self):
  with patch.dict(os.environ,CONFIG,clear=True),patch('deploy.subprocess.run',side_effect=RuntimeError('SSH failed')) as run:
   with self.assertRaises(RuntimeError): deploy.main()
   self.assertEqual(run.call_count,1)
 def test_live_deployment_requires_exact_html(self):
  with patch.dict(os.environ,dict(CONFIG,DRY_RUN='false'),clear=True),patch('deploy.subprocess.run') as run,patch('deploy.urlopen') as web,patch('deploy.time.sleep'):
   web.return_value.__enter__.return_value.read.return_value=b'Wrong website'
   with self.assertRaisesRegex(RuntimeError,'live HTML verification failed'): deploy.main()
   self.assertNotIn('--dry-run',run.call_args_list[-1].args[0])
 def test_live_deployment_checks_all_four_pages(self):
  with patch.dict(os.environ,dict(CONFIG,DRY_RUN='false'),clear=True),patch('deploy.subprocess.run'),patch('deploy.urlopen') as web:
   web.return_value.__enter__.return_value.read.side_effect=[(deploy.ROOT/page).read_bytes() for page in deploy.DEMO_PAGES]
   deploy.main();self.assertEqual(web.call_count,len(deploy.DEMO_PAGES))
 def test_marketing_target_is_exact_parent_only(self):
  c=deploy.settings(dict(CONFIG,DEPLOY_SITE='marketing'))
  self.assertEqual(c['HOSTINGER_TARGET_DIR'],'/home/u123/domains/bleenky.com/public_html')
  self.assertEqual(c['DEMO_BASE_URL'],'https://bleenky.com/')
  for target in ['/home/u123/domains/other.com/public_html/demos','/home/u123/domains/bleenky.com/public_html','/home/u123/domains/bleenky.com/public_html/demos/other']:
   with self.assertRaises(ValueError): deploy.settings(dict(CONFIG,DEPLOY_SITE='marketing',HOSTINGER_TARGET_DIR=target))
 def test_unknown_profile_rejected(self):
  with self.assertRaises(ValueError): deploy.settings(dict(CONFIG,DEPLOY_SITE='typo'))
 def test_marketing_dry_run_protects_demos(self):
  with patch.dict(os.environ,dict(CONFIG,DEPLOY_SITE='marketing',DRY_RUN='true'),clear=True),patch('deploy.subprocess.run') as run,patch('deploy.urlopen') as web:
   deploy.main();args=run.call_args_list[-1].args[0]
   self.assertIn('--exclude=/demos/',args)
   self.assertIn('--dry-run',args);self.assertNotIn('--delete',args)
   self.assertTrue(args[-2].endswith('/marketing/'))
   self.assertEqual(args[-1],'u123@example.com:/home/u123/domains/bleenky.com/public_html/')
   web.assert_not_called()
 def test_marketing_checks_all_four_pages(self):
  with patch.dict(os.environ,dict(CONFIG,DEPLOY_SITE='marketing',DRY_RUN='false'),clear=True),patch('deploy.subprocess.run'),patch('deploy.urlopen') as web:
   web.return_value.__enter__.return_value.read.side_effect=[(deploy.ROOT.parent/'marketing'/p).read_bytes() for p in deploy.MARKETING_PAGES]
   deploy.main();self.assertEqual(web.call_count,4)
   self.assertEqual(web.call_args_list[1].args[0].full_url,'https://bleenky.com/service-guide.html?bleenky_deploy=123')
if __name__=='__main__': unittest.main()
