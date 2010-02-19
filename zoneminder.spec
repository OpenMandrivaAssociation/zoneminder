%define zmuid $(id -un)
%define zmgid $(id -gn)
%define zmuid_final apache
%define zmgid_final apache

Name:		zoneminder
Version:	1.24.2
Release:	%mkrel 1
Summary:	A camera monitoring and analysis tool
Group:		Monitoring
# jscalendar is LGPL (any version):  http://www.dynarch.com/projects/calendar/
# Mootools is inder the MIT license: http://mootools.net/
License:	GPLv2+ and LGPLv2+ and MIT 
URL:		http://www.zoneminder.com/
Source:		http://www.zoneminder.com/fileadmin/downloads/ZoneMinder-%{version}.tar.gz
Source1:	http://www.charliemouse.com/code/cambozola/cambozola-0.68.tar.gz
Source2:	zoneminder.conf
Source5:	http://downloads.sourceforge.net/jscalendar/jscalendar-1.0.zip
Source6:	http://mootools.net/download/get/mootools-1.2.3-core-yc.js
Patch1:		zoneminder-1.24.2-dbinstall.patch
Patch2:		zoneminder-1.24.2-noffmpeg.patch
Patch3:		zoneminder-1.24.1-perldep.patch
Patch4:		zoneminder-1.22.3-installfix.patch
Patch5:		zoneminder-1.24.2-gcc44.patch
# (ahmad) upstream patch to fix build with new jpeg
Patch6:		zoneminder-1.24.2-jpeg.patch
Patch7:		zoneminder-1.24.2-fix-str-fmt.patch

BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires:	automake gnutls-devel
BuildRequires:	mysql-devel pcre-devel libjpeg-devel
BuildRequires:	perl(Archive::Tar) perl(Archive::Zip)
BuildRequires:	perl(Date::Manip) perl(DBD::mysql)
BuildRequires:	perl(ExtUtils::MakeMaker) perl(LWP::UserAgent)
BuildRequires:	perl(MIME::Entity) perl(MIME::Lite)
BuildRequires:	perl(PHP::Serialization)
Requires:	httpd php php-mysql
Requires:	perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
Requires:	perl(DBD::mysql) perl(Archive::Tar) perl(Archive::Zip)
Requires:	perl(MIME::Entity) perl(MIME::Lite) perl(Net::SMTP) perl(Net::FTP) 

Requires(post):	rpm-helper
Requires(preun): rpm-helper

 
%description
ZoneMinder is a set of applications which is intended to provide a complete
solution allowing you to capture, analyse, record and monitor any cameras you
have attached to a Linux based machine. It is designed to run on kernels which
support the Video For Linux (V4L) interface and has been tested with cameras
attached to BTTV cards, various USB cameras and IP network cameras. It is
designed to support as many cameras as you can attach to your computer without
too much degradation of performance. This package includes cambozola.jar.


%prep
%setup -q -n ZoneMinder-%{version}

# Unpack jscalendar and move some files around
%setup -q -D -T -a 5 -n ZoneMinder-%{version}
mkdir jscalendar-doc
pushd jscalendar-1.0
mv *html *php doc/* README ../jscalendar-doc
rm -fr doc
popd

%patch1 -p0 -b .dbinstall
%patch2 -p0 -b .noffmpeg
%patch3 -p0 -b .perldep
%patch4 -p0 -b .installfix
%patch5 -p0 -b .gcc44
%patch6 -p1 -b .jpeg
%patch7 -p0 -b .str
tar xf %{SOURCE1} --wildcards  cambozola-*/dist/cambozola.jar

cat <<EOF >> db/zm_create.sql.in
update Config set Value = '/cgi-bin/zm/nph-zms' where Name = 'ZM_PATH_ZMS';
use mysql;
grant select,insert,update,delete on zm.* to 'zmuser'@localhost identified by 'zmpass';
EOF

autoreconf -fi

%build
%configure \
	--with-libarch=%{_lib} \
	--with-mysql=%{_prefix} \
	--with-webdir=%{_datadir}/%{name}/www \
	--with-cgidir=%{_libexecdir}/%{name}/cgi-bin \
	--with-webuser=%{zmuid} \
	--with-webgroup=%{zmgid} \
	--disable-debug \
	--disable-mmap

%make
%{__perl} -pi -e 's/(ZM_WEB_USER=).*$/${1}%{zmuid_final}/;' \
	      -e 's/(ZM_WEB_GROUP=).*$/${1}%{zmgid_final}/;' zm.conf


%install
rm -rf %{buildroot}

install -d %{buildroot}%{_localstatedir}/run
make install DESTDIR=%{buildroot} 

rm -f %{buildroot}%{_bindir}/zmx10.pl

# fix mandir loction manually, it insists on /usr/local
mkdir -p %{buildroot}%{_mandir}
mv %{buildroot}/usr/local/share/man/man3 %{buildroot}%{_mandir}
rm -fr %{buildroot}/usr/local/share/man

install -m 755 -d %{buildroot}%{_localstatedir}/log/zoneminder
for dir in events images temp
do
	install -m 755 -d %{buildroot}%{_localstatedir}/lib/zoneminder/$dir
	rmdir %{buildroot}%{_datadir}/%{name}/www/$dir
	ln -sf ../../../..%{_localstatedir}/lib/zoneminder/$dir %{buildroot}%{_datadir}/%{name}/www/$dir
done
install -D -m 755 scripts/zm %{buildroot}%{_initrddir}/zoneminder
install -D -m 644 cambozola-*/dist/cambozola.jar %{buildroot}%{_datadir}/%{name}/www/cambozola.jar
install -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/httpd/conf.d/zoneminder.conf


# Install jscalendar - this really should be in its own package
install -d -m 755 %{buildroot}%{_datadir}/%{name}/www/jscalendar
cp -rp jscalendar-1.0/* %{buildroot}%{_datadir}/%{name}/www/jscalendar

# Install mootools
pushd %{buildroot}%{_datadir}/%{name}/www
install -m 644 %{SOURCE6} mootools-1.2.3-core-yc.js
ln -s mootools-1.2.3-core-yc.js mootools.js
popd

# logrotate
install -D -m 0644 scripts/zmlogrotate.conf %{buildroot}%{_sysconfdir}/logrotate.d/zoneminder

%clean
rm -rf %{buildroot}


%post
%_post_service zoneminder


%preun
%_preun_service zoneminder


%files
%defattr(-,root,root,-)
%doc AUTHORS COPYING README jscalendar-doc
%config(noreplace) %attr(640,root,%{zmgid_final}) %{_sysconfdir}/zm.conf
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/httpd/conf.d/zoneminder.conf
%attr(755,root,root) %{_initrddir}/zoneminder
%config(noreplace) %{_sysconfdir}/logrotate.d/zoneminder
%{_bindir}/zma
%{_bindir}/zmaudit.pl
%{_bindir}/zmc
%{_bindir}/zmcontrol.pl
%{_bindir}/zmdc.pl
%{_bindir}/zmf
%{_bindir}/zmfilter.pl
%attr(4755,root,root) %{_bindir}/zmfix
%{_bindir}/zmpkg.pl
%{_bindir}/zmtrack.pl
%{_bindir}/zmtrigger.pl
%{_bindir}/zmu
%{_bindir}/zmupdate.pl
%{_bindir}/zmvideo.pl
%{_bindir}/zmwatch.pl
%{perl_sitelib}/ZoneMinder*
%{_mandir}/man*/*
%dir %{_libexecdir}/%{name}
%{_libexecdir}/%{name}/cgi-bin
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/db
%{_datadir}/%{name}/www

%dir %attr(755,%{zmuid_final},%{zmgid_final}) %{_localstatedir}/lib/zoneminder
%dir %attr(755,%{zmuid_final},%{zmgid_final}) %{_localstatedir}/lib/zoneminder/events
%dir %attr(755,%{zmuid_final},%{zmgid_final}) %{_localstatedir}/lib/zoneminder/images
%dir %attr(755,%{zmuid_final},%{zmgid_final}) %{_localstatedir}/lib/zoneminder/temp
%dir %attr(755,%{zmuid_final},%{zmgid_final}) %{_localstatedir}/log/zoneminder
