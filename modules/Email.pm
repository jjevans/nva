use strict;
use warnings;

package Email;

use Exporter qw(import);
use MIME::Lite;

our @EXPORT_OK = qw(send_email_with_attachment);

sub new{
        my $class = shift;

        my $email = {
                "to_email" => shift,
                "from_address" => shift,
                "subject" => shift,
                "msg_body" => shift
        };

        bless($email, $class);

        return $email;
}

sub send_email_with_attachment{

        my ($email, $filepath, $filename) = @_;

        my $msg = MIME::Lite->new(
            From    => $email->{"from_address"},
            To      => $email->{"to_email"},
            Subject => $email->{"subject"},
            Type    => 'multipart/mixed',
        );

        $msg->attach(
            Type     => 'TEXT',
            Data     => $email->{"msg_body"},
        );

        $msg->attach(
            Type     => 'application/vnd.ms-excel',
            Path     => $filepath . $filename,
            Filename => $filename
        );

        $msg->send();
}



1;