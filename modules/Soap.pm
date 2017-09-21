use strict;
use warnings;

package Soap;

use Exporter qw(import);
use MIME::Lite;

our @EXPORT_OK = qw(soap_call soap_auth);

sub new{
        my $class = shift;

        my $soap_params = {
                "namespace" => shift,
                "endpoint" => shift,
                "username" => shift,
                "password" => shift,
        };

        bless($soap_params, $class);

        return $soap_params;
}

sub soap_call{

                my ($soap_params) = @_;

                my $soap = SOAP::Lite->uri($soap_params->{"namespace"})->proxy($soap_params->{"endpoint"})->on_fault(
            sub {    # SOAP fault handler
                my $soap = shift;
                my $res  = shift;

                # Map faults to exceptions
                if ( ref($res) eq '' ) {
                    die($res);
                }
                else {
                    die( $res->faultstring );
                }
            }
        );

        $soap->ns('http://pcpgm.partners.org/geneinsight', 'gen');

        $soap->serializer()->register_ns( 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
'wsse' );

        return $soap;
}

sub soap_auth {

        my ($soap_params) = @_;

        my $auth = SOAP::Header->name('wsse:Security' =>
                                            \SOAP::Data->name("wsse:UsernameToken" =>
                                                \SOAP::Data->value(
                                                    SOAP::Data->name("wsse:Username" => $soap_params->{"username"})->type(''),
                                                    SOAP::Data->name("wsse:Password" => $soap_params->{"password"})->type('')->
attr({'Type'=>'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText'})
                                                )
                                            )
                                        );
    return $auth;

}

1;