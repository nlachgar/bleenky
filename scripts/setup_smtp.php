<?php
// CLI only. Install at ~/.bleenky-mail/setup.php, never in public_html.
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
ini_set('display_errors', '0');
umask(0077);
$directory = '/home/u496265211/.bleenky-mail';
$temp = null;
try {
    define('BLEENKY_CONTACT_TEST', true);
    require '/home/u496265211/domains/bleenky.com/public_html/contact.php';
    require $directory.'/vendor/autoload.php';
    $config = json_decode(stream_get_contents(STDIN, 4096), true, 8, JSON_THROW_ON_ERROR);
    $mailer = contact_smtp_mailer($config);
    // Authenticate without sending any email. Failure leaves existing config intact.
    if (!$mailer->smtpConnect()) throw new RuntimeException('Connection failed');
    $mailer->smtpClose();
    $temp = tempnam($directory, '.config-');
    if ($temp === false || !chmod($temp, 0600)) throw new RuntimeException('Cannot create private config');
    $json = json_encode(['username'=>$config['username'], 'password'=>$config['password']], JSON_THROW_ON_ERROR);
    if (file_put_contents($temp, $json, LOCK_EX) !== strlen($json)) throw new RuntimeException('Cannot save configuration');
    if (!rename($temp, $directory.'/config.json')) throw new RuntimeException('Cannot activate configuration');
    $temp = null;
    echo "SMTP login verified. Private configuration saved. The contact form now uses SMTP.\n";
} catch (Throwable $e) {
    if (is_string($temp) && is_file($temp)) unlink($temp);
    // Never print exception details: SMTP errors can contain account information.
    fwrite(STDERR, "SMTP setup failed. Existing configuration was kept. Check the mailbox password and try again; if it still fails, ask for a connection check.\n");
    exit(1);
}
