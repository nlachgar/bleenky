<?php
declare(strict_types=1);

function contact_validate(array $input): array {
    $limits = ['name'=>100, 'email'=>254, 'salon'=>150, 'website'=>500, 'interest'=>80, 'message'=>3000, 'company_url'=>500];
    $data = [];
    foreach ($limits as $key=>$limit) {
        $value = $input[$key] ?? '';
        if (!is_string($value) || strlen($value)>$limit) throw new InvalidArgumentException('Please check the length and format of your details.');
        $data[$key] = trim($value);
    }
    if ($data['company_url']!=='') throw new InvalidArgumentException('Unable to submit this form. Please email us instead.');
    foreach (['name','email','salon','interest','message'] as $key) {
        if ($data[$key]==='') throw new InvalidArgumentException('Please complete all required fields.');
    }
    if (!filter_var($data['email'], FILTER_VALIDATE_EMAIL) || preg_match('/[\r\n]/', $data['email'])) throw new InvalidArgumentException('Enter a valid email address.');
    if (!in_array($data['interest'], ['Website & Care', 'Separate booking service', 'Something else'], true)) throw new InvalidArgumentException('Choose an interest from the list.');
    return $data;
}

function contact_send(array $data, callable $send): bool {
    $body = "New Bleenky interest form\n\n";
    foreach (['name'=>'Name','email'=>'Reply email','salon'=>'Salon','website'=>'Current website','interest'=>'Interested in','message'=>'Message'] as $key=>$label) {
        $body .= $label . ': ' . $data[$key] . "\n\n";
    }
    return $send('hello@bleenky.com', 'Bleenky website inquiry', $body, [
        'From'=>'Bleenky Website <hello@bleenky.com>',
        'Reply-To'=>$data['email'],
        'MIME-Version'=>'1.0',
        'Content-Type'=>'text/plain; charset=UTF-8'
    ]);
}

// Credentials and dependencies live outside public_html and outside Git.
function contact_smtp_mailer(array $config, ?callable $factory = null): object {
    if (($config['username'] ?? '') !== 'hello@bleenky.com' || !is_string($config['password'] ?? null) || $config['password'] === '' || strlen($config['password']) > 1024) {
        throw new RuntimeException('SMTP configuration unavailable');
    }
    $mailer = $factory ? $factory() : new \PHPMailer\PHPMailer\PHPMailer(true);
    $mailer->isSMTP();
    $mailer->Host = 'smtp.hostinger.com';
    $mailer->Port = 465;
    $mailer->SMTPSecure = 'ssl';
    $mailer->SMTPAuth = true;
    $mailer->Username = $config['username'];
    $mailer->Password = $config['password'];
    $mailer->SMTPDebug = 0;
    $mailer->Timeout = 20;
    $mailer->CharSet = 'UTF-8';
    $mailer->SMTPOptions = ['ssl'=>['verify_peer'=>true, 'verify_peer_name'=>true, 'allow_self_signed'=>false]];
    $mailer->setFrom('hello@bleenky.com', 'Bleenky Website');
    $mailer->addAddress('hello@bleenky.com');
    return $mailer;
}

function contact_smtp_send(object $mailer, string $subject, string $body, string $replyTo): bool {
    $mailer->addReplyTo($replyTo);
    $mailer->Subject = $subject;
    $mailer->Body = $body;
    $mailer->isHTML(false);
    return $mailer->send();
}

function contact_deliver(array $data, string $directory): bool {
    // Preserve existing delivery until the credential setup succeeds. Never fall
    // back to unauthenticated mail after SMTP is configured or fails.
    $file = $directory.'/config.json';
    if (!file_exists($file)) {
        return contact_send($data, fn($to,$subject,$body,$headers)=>mail($to,$subject,$body,$headers,'-fhello@bleenky.com'));
    }
    if (is_link($file) || (fileperms($file) & 0077) !== 0) throw new RuntimeException('Unsafe SMTP configuration permissions');
    $config = json_decode(file_get_contents($file), true, 8, JSON_THROW_ON_ERROR);
    require_once $directory.'/vendor/autoload.php';
    $mailer = contact_smtp_mailer($config);
    return contact_send($data, fn($to,$subject,$body,$headers)=>contact_smtp_send($mailer,$subject,$body,$headers['Reply-To']));
}

// Store only short-lived rate-limit timestamps and hashed addresses, never inquiry bodies.
function contact_rate_limit(string $directory, string $ip, int $now): bool {
    if (!is_dir($directory) && !mkdir($directory, 0700, true) && !is_dir($directory)) throw new RuntimeException('Rate limiter unavailable');
    $file = $directory.'/limits.json';
    $handle = fopen($file, 'c+');
    if (!$handle || !flock($handle, LOCK_EX)) throw new RuntimeException('Rate limiter unavailable');
    chmod($file, 0600);
    try {
        $rows = json_decode(stream_get_contents($handle), true) ?: [];
        $rows = array_values(array_filter($rows, fn($row)=>is_array($row) && ($row['time']??0)>$now-3600));
        $hash = hash('sha256', $ip);
        $perIp = count(array_filter($rows, fn($row)=>($row['ip']??'')===$hash));
        $recent = count(array_filter($rows, fn($row)=>$row['time']>$now-60));
        if ($perIp>=5 || count($rows)>=50 || $recent>=5) return false;
        $rows[] = ['ip'=>$hash, 'time'=>$now];
        rewind($handle);ftruncate($handle, 0);fwrite($handle, json_encode($rows));fflush($handle);
        return true;
    } finally {flock($handle, LOCK_UN);fclose($handle);}
}

if (defined('BLEENKY_CONTACT_TEST')) return;
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store, private');
header('X-Content-Type-Options: nosniff');
function contact_reply(int $code, array $body): never {http_response_code($code);echo json_encode($body);exit;}
$method = $_SERVER['REQUEST_METHOD'] ?? '';
if (!in_array($method, ['GET','POST'], true)) {header('Allow: GET, POST');contact_reply(405,['error'=>'Method not allowed.']);}
if ((int)($_SERVER['CONTENT_LENGTH']??0)>12000) contact_reply(413,['error'=>'Your message is too long. Please shorten it and try again.']);
if (!empty($_SERVER['HTTP_ORIGIN']) && !in_array($_SERVER['HTTP_ORIGIN'], ['https://bleenky.com','https://www.bleenky.com'], true)) contact_reply(403,['error'=>'Please use the form on bleenky.com.']);
session_name('bleenky_contact');
session_start(['cookie_secure'=>true,'cookie_httponly'=>true,'cookie_samesite'=>'Strict','cookie_path'=>'/','use_strict_mode'=>true]);
if ($method==='GET') {
    if (empty($_SESSION['contact_token'])) $_SESSION['contact_token']=bin2hex(random_bytes(32));
    contact_reply(200,['token'=>$_SESSION['contact_token']]);
}
try {
    $raw = file_get_contents('php://input', false, null, 0, 12001);
    if (strlen($raw)>12000) contact_reply(413,['error'=>'Your message is too long.']);
    $input = json_decode($raw, true);
    if (!is_array($input)) contact_reply(400,['error'=>'Please check your form and try again.']);
    if (!is_string($input['token']??null) || empty($_SESSION['contact_token']) || !hash_equals($_SESSION['contact_token'],$input['token'])) contact_reply(403,['error'=>'Your form session expired. Please refresh and try again.']);
    $data = contact_validate($input);
    if (!contact_rate_limit(dirname(__DIR__,3).'/.bleenky-contact-state', $_SERVER['REMOTE_ADDR']??'unknown', time())) contact_reply(429,['error'=>'Too many attempts. Please wait an hour or email hello@bleenky.com.']);
    if (!contact_deliver($data, dirname(__DIR__,3).'/.bleenky-mail')) contact_reply(503,['error'=>'We could not send your inquiry. Your details are still here; please retry or email hello@bleenky.com.']);
    unset($_SESSION['contact_token']);
    contact_reply(200,['ok'=>true,'message'=>'Thanks! Your inquiry has been sent. We aim to reply within two business days. If you do not hear from us, email hello@bleenky.com.']);
} catch (InvalidArgumentException $e) {contact_reply(422,['error'=>$e->getMessage()]);}
catch (Throwable $e) {error_log('Bleenky contact: delivery unavailable');contact_reply(503,['error'=>'We could not send your inquiry. Please email hello@bleenky.com.']);}
