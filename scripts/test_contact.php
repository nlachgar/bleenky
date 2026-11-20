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

class FakeSmtpMailer extends stdClass {
    public bool $result = true;
    public bool $throws = false;
    public function isSMTP(): void {$this->transport='smtp';}
    public function setFrom($address,$name): void {$this->from=$address;}
    public function addAddress($address): void {$this->to=$address;}
    public function addReplyTo($address): void {$this->reply=$address;}
    public function isHTML($value): void {$this->html=$value;}
    public function send(): bool {if($this->throws)throw new RuntimeException('Simulated SMTP failure');return $this->result;}
}
$fake = contact_smtp_mailer(['username'=>'hello@bleenky.com','password'=>'fake-test-only'], fn()=>new FakeSmtpMailer());
check($fake->transport==='smtp' && $fake->Host==='smtp.hostinger.com' && $fake->Port===465 && $fake->SMTPSecure==='ssl', 'Encrypted SMTP');
check($fake->SMTPAuth && $fake->SMTPDebug===0 && $fake->SMTPOptions['ssl']['verify_peer'] && $fake->SMTPOptions['ssl']['verify_peer_name'] && !$fake->SMTPOptions['ssl']['allow_self_signed'], 'Authentication, certificate validation, no credential logging');
check($fake->from==='hello@bleenky.com' && $fake->to==='hello@bleenky.com', 'Fixed SMTP sender and recipient');
check(contact_send($data, fn($to,$subject,$body,$headers)=>contact_smtp_send($fake,$subject,$body,$headers['Reply-To'])), 'SMTP success');
check($fake->reply==='test@example.com' && $fake->Subject==='Bleenky website inquiry' && str_contains($fake->Body,'Sample Salon') && !$fake->html, 'SMTP message and visitor reply');
$fake->result=false;
check(!contact_smtp_send($fake,'Test','Test','test@example.com'), 'SMTP rejection propagates');
$fake->throws=true;
$threw=false;try{contact_smtp_send($fake,'Test','Test','test@example.com');}catch(RuntimeException $e){$threw=true;}check($threw,'SMTP exception propagates');
foreach ([[],['username'=>'other@example.com','password'=>'fake'],['username'=>'hello@bleenky.com','password'=>'']] as $config) {
 $threw=false;try{contact_smtp_mailer($config,fn()=>new FakeSmtpMailer());}catch(RuntimeException $e){$threw=true;}check($threw,'Reject bad SMTP config');
}
$directory=sys_get_temp_dir().'/bleenky-smtp-test-'.bin2hex(random_bytes(6));mkdir($directory,0700);
try {
 file_put_contents($directory.'/config.json','invalid json');chmod($directory.'/config.json',0600);
 $threw=false;try{contact_deliver($data,$directory);}catch(Throwable $e){$threw=true;}check($threw,'Broken SMTP config must not fall back to PHP mail');
 chmod($directory.'/config.json',0644);clearstatcache();
 $threw=false;try{contact_deliver($data,$directory);}catch(RuntimeException $e){$threw=true;}check($threw,'Reject publicly readable credentials');
} finally {unlink($directory.'/config.json');rmdir($directory);}
echo "SMTP tests passed: TLS, fixed addresses, reply-to, errors, private configuration, no fallback after activation.\n";
