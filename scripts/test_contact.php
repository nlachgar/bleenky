<?php
define('BLEENKY_CONTACT_TEST', true);
require __DIR__.'/../marketing/contact.php';
function check(bool $ok,string $message): void {if(!$ok) throw new RuntimeException($message);}
$good=['name'=>'Test User','email'=>'test@example.com','salon'=>'Sample Salon','website'=>'example.com','interest'=>'Website & Care','message'=>'Please tell me more.','company_url'=>''];
$data=contact_validate($good);check($data['name']==='Test User','Valid inquiry');
foreach ([['email'=>"test@example.com\r\nBcc:bad@example.com"],['name'=>[]],['message'=>''],['message'=>str_repeat('a',3001)],['interest'=>'Not an option'],['company_url'=>'spam']] as $patch) {
    $failed=false;try{contact_validate(array_replace($good,$patch));}catch(InvalidArgumentException $e){$failed=true;}check($failed,'Invalid submission accepted');
}
$sent=false;
check(contact_send($data,function($to,$subject,$body,$headers) use (&$sent){
    check($to==='hello@bleenky.com','Recipient must be fixed');
    check($headers['Reply-To']==='test@example.com','Reply address');
    check(str_contains($body,'Sample Salon'),'Inquiry body');$sent=true;return true;
}), 'Send success');check($sent,'Mailer called');
check(contact_send($data,fn()=>false)===false,'Delivery failure must propagate');
$directory=sys_get_temp_dir().'/bleenky-contact-test-'.bin2hex(random_bytes(6));
try {
 for($i=0;$i<5;$i++)check(contact_rate_limit($directory,'192.0.2.1',10000+$i*61),'Valid rate');
 check(!contact_rate_limit($directory,'192.0.2.1',10400),'Per-IP limit');
 check(contact_rate_limit($directory,'192.0.2.1',14000),'Expiry');
 $stored=file_get_contents($directory.'/limits.json');check(!str_contains($stored,'192.0.2.1')&&!str_contains($stored,'Sample Salon'),'Do not store raw address or inquiry');
}finally{if(file_exists($directory.'/limits.json'))unlink($directory.'/limits.json');if(is_dir($directory))rmdir($directory);}
echo "Contact tests passed: validation, injection, fixed recipient, delivery failure, rate limiting, expiry, minimal storage.\n";
