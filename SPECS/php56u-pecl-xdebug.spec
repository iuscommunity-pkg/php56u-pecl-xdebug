%global pecl_name xdebug
%global php_base  php56u
%global with_zts  0%{?__ztsphp:1}
# XDebug should be loaded after opcache
%global ini_name  15-%{pecl_name}.ini

Name:           %{php_base}-pecl-xdebug
Summary:        PECL package for debugging PHP scripts
Version:        2.5.5
Release:        1.ius%{?dist}
Source0:        http://pecl.php.net/get/%{pecl_name}-%{version}.tgz

# The Xdebug License, version 1.01
# (Based on "The PHP License", version 3.0)
License:        PHP
Group:          Development/Languages
URL:            http://xdebug.org/

BuildRequires:  %{php_base}-pear
BuildRequires:  %{php_base}-devel
BuildRequires:  libedit-devel
BuildRequires:  libtool

Requires(post): %{php_base}-pear
Requires(postun): %{php_base}-pear

Requires:       %{php_base}(zend-abi) = %{php_zend_api}
Requires:       %{php_base}(api) = %{php_core_api}

# provide the stock name
Provides:       php-pecl-%{pecl_name} = %{version}
Provides:       php-pecl-%{pecl_name}%{?_isa} = %{version}

# provide the stock and IUS names without pecl
Provides:       php-%{pecl_name} = %{version}
Provides:       php-%{pecl_name}%{?_isa} = %{version}
Provides:       %{php_base}-%{pecl_name} = %{version}
Provides:       %{php_base}-%{pecl_name}%{?_isa} = %{version}

# provide the stock and IUS names in pecl() format
Provides:       php-pecl(Xdebug) = %{version}
Provides:       php-pecl(Xdebug)%{?_isa} = %{version}
Provides:       %{php_base}-pecl(Xdebug) = %{version}
Provides:       %{php_base}-pecl(Xdebug)%{?_isa} = %{version}

# conflict with the stock name
Conflicts:      php-pecl-%{pecl_name} < %{version}

%{?filter_provides_in: %filter_provides_in %{php_extdir}/.*\.so$}
%{?filter_provides_in: %filter_provides_in %{php_ztsextdir}/.*\.so$}
%{?filter_setup}


%description
The Xdebug extension helps you debugging your script by providing a lot of
valuable debug information. The debug information that Xdebug can provide
includes the following:

* stack and function traces in error messages with:
  o full parameter display for user defined functions
  o function name, file name and line indications
  o support for member functions
* memory allocation
* protection for infinite recursions

Xdebug also provides:

* profiling information for PHP scripts
* code coverage analysis
* capabilities to debug your scripts interactively with a debug client


%prep
%setup -qc
mv %{pecl_name}-%{version} NTS

sed -e '/LICENSE/s/role="doc"/role="src"/' -i package.xml

pushd NTS

# Check extension version
ver=$(sed -n '/XDEBUG_VERSION/{s/.* "//;s/".*$//;p}' php_xdebug.h)
if test "$ver" != "%{version}"; then
   : Error: Upstream XDEBUG_VERSION version is ${ver}, expecting %{version}.
   exit 1
fi

popd

%if %{with_zts}
# Duplicate source tree for NTS / ZTS build
cp -pr NTS ZTS
%endif

cat > %{ini_name} << EOF
; Enable %{pecl_name} extension module
zend_extension=%{pecl_name}.so

; see http://xdebug.org/docs/all_settings
EOF
sed -e '1d' NTS/%{pecl_name}.ini >> %{ini_name}


%build
pushd NTS
%{_bindir}/phpize
%configure \
    --enable-xdebug  \
    --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

# Build debugclient
pushd debugclient
./buildconf
%configure --with-libedit
make %{?_smp_mflags}
popd
popd

%if %{with_zts}
pushd ZTS
%{_bindir}/zts-phpize
%configure \
    --enable-xdebug  \
    --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
popd
%endif


%install
# install NTS extension
make -C NTS install INSTALL_ROOT=%{buildroot}
install -Dpm 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# install debugclient
install -Dpm 755 NTS/debugclient/debugclient \
        %{buildroot}%{_bindir}/debugclient

# install package registration file
install -Dpm 644 package.xml %{buildroot}%{pecl_xmldir}/%{pecl_name}.xml

%if %{with_zts}
# Install ZTS extension
make -C ZTS install INSTALL_ROOT=%{buildroot}
install -Dpm 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Documentation
for i in $(grep 'role="doc"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 NTS/$i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


%check
# only check if build extension can be loaded
%{__php} \
    --no-php-ini \
    --define zend_extension=%{buildroot}%{php_extdir}/%{pecl_name}.so \
    --modules | grep Xdebug

%if %{with_zts}
%{__ztsphp} \
    --no-php-ini \
    --define zend_extension=%{buildroot}%{php_ztsextdir}/%{pecl_name}.so \
    --modules | grep Xdebug
%endif


%post
%{pecl_install} %{pecl_xmldir}/%{pecl_name}.xml >/dev/null || :


%postun
if [ $1 -eq 0 ]; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%files
%license NTS/LICENSE
%doc %{pecl_docdir}/%{pecl_name}
%{_bindir}/debugclient
%{pecl_xmldir}/%{pecl_name}.xml

%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{pecl_name}.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{pecl_name}.so
%endif


%changelog
* Wed Jun 21 2017 Ben Harper <ben.harper@rackspace.com> - 5.2.5.1.ius
- Latest upstream

* Mon May 15 2017 Ben Harper <ben.harper@rackspace.com> - 5.2.4-1.ius
- Latest upstream

* Tue Apr 18 2017 Ben Harper <ben.harper@rackspace.com> - 5.2.3-1.ius
- Latest upstream

* Mon Feb 27 2017 Carl George <carl.george@rackspace.com> - 2.5.1-1.ius
- Latest upstream
- Install package.xml as %%{pecl_name}.xml, not %%{name}.xml
- Don't install/register LICENSE during %%prep
- Generate ini file during %%prep
- Use uptream provided configuration with all settings (Fedora)

* Mon Dec 05 2016 Ben Harper <ben.harper@rackspace.com> - 2.5.0-1.ius
- Latest upstream

* Tue Aug 02 2016 Ben Harper <ben.harper@rackspace.com> - 2.4.1-1.ius
- Latest upstream

* Thu Jun 16 2016 Ben Harper <ben.harper@rackspace.com> - 2.4.0-3.ius
- update filters to include zts

* Tue Mar 08 2016 Carl George <carl.george@rackspace.com> - 2.4.0-2.ius
- Re-add scriptlets, file triggers aren't available in EL version of RPM

* Mon Mar 07 2016 Carl George <carl.george@rackspace.com> - 2.4.0-1.ius
- Latest upstream
- Use %%license on LICENSE file
- Drop scriptlets, replaced by file triggers in php56u-pear (Fedora)

* Tue Jun 30 2015 Carl George <carl.george@rackspace.com> - 2.3.3-1.ius
- Latest upstream

* Wed Mar 25 2015 Carl George <carl.george@rackspace.com> - 2.3.2-1.ius
- Latest upstream
- Include license

* Tue Mar 10 2015 Ben Harper <ben.harper@rackspace.com> - 2.3.0-2.ius
- Rebuilding against php56u-5.6.6-2.ius as it is now using bundled PCRE.

* Mon Feb 23 2015 Ben Harper <ben.harper@rackspace.com> - 2.3.0-1.ius
- porting fomr php55u-pecl-xdebug
- add if for filter_provides_in

* Mon Feb 23 2015 Carl George <carl.george@rackspace.com> - 2.3.0-1.ius
- Latest upstream

* Thu Jan 22 2015 Ben Harper <ben.harper@rackspace.com> - 2.2.7-1.ius
- Latest sources from upstream

* Mon Nov 17 2014 Carl George <carl.george@rackspace.com> - 2.2.6-1.ius
- Latest sources from upstream

* Fri Oct 10 2014 Carl George <carl.george@rackspace.com> - 2.2.5-2.ius
- Directly require the correct pear package, not /usr/bin/pecl
- Conflict with stock package
- Add missing provides
- Add numerical prefix to extension configuration file
- Drop uneeded full extension path
- Move documentation to pecl_docdir
- Enable ZTS build
- Fix License which is PHP, with some renaming
- Add filter_provides to avoid private-shared-object-provides xdebug.so
- Add minimal load test
- Build with libedit

* Wed Apr 30 2014 Carl George <carl.george@rackspace.com> - 2.2.5-1.ius
- Latest sources from upstream

* Mon Mar 03 2014 Ben Harper <ben.harper@rackspace.com> - 2.2.4-1.ius
- Latest sources from upstream

* Fri Jan 24 2014 Ben Harper <ben.harper@rackspace.com> - 2.2.3-2.ius
- porting from php54-pecl-xdebug

* Wed May 22 2013 Ben Harper <ben.harper@rackspace.com> - 2.2.3-1.ius
- Latest sources from upstream

* Mon Mar 25 2013 Ben Harper <ben.harper@rackspace.com> - 2.2.2-1.ius
- Latest sources from upstream

* Tue Aug 21 2012 Jeffrey Ness <jeffrey.ness@rackspace.com> - 2.2.1-2
- Rebuilding against php54-5.4.6-2.ius as it is now using bundled PCRE.

* Mon Jul 16 2012 Dustin Henry Offutt <dustin.offutt@rackspace.com> 2.2.1-1
- Latest sources from upstream

* Fri May 11 2012 Dustin Henry Offutt <dustin.offutt@rackspace.com> 2.2.0-2
- Build for php54

* Sat May 05 2012 Dustin Henry Offutt <dustin.offutt@rackspace.com> 2.2.0-1
- Latest sources from upstream
- Remove expectation of file "Changelog" which file "NEWS" now covers, according to the pecl-xdebug project (http://bugs.xdebug.org/view.php?id=828)

* Wed Mar 14 2012 Jeffrey Ness <jeffrey.ness@rackspace.com> 2.1.4-1
- Latest sources from upstream

* Thu Jan 26 2012 Jeffrey Ness <jeffrey.ness@rackspace.com> 2.1.3-1
- Latest sources from upstream

* Fri Aug 19 2011 Jeffrey Ness <jeffrey.ness@rackspace.com> 2.1.2-2
- Rebuilding

* Fri Jul 29 2011 Jeffrey Ness <jeffrey.ness@rackspace.com> 2.1.2-1
- Latest sources from upstream

* Mon Apr 4 2011 Jeffrey Ness <jeffrey.ness@rackspace.com> 2.1.1-1
- Latest sources from upstream
- Removed Patch0: %%{pecl_name}-2.0.3-codecoverage.patch

* Mon Jan 24 2011 Jeffrey Ness <jeffrey.ness@rackspace.com> 2.0.5-2
- Porting from EPEL to IUS

* Mon Sep 14 2009 Christopher Stone <chris.stone@gmail.com> 2.0.5-1.1
- Upstream sync

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sun Jul 12 2009 Remi Collet <Fedora@FamilleCollet.com> - 2.0.4-1
- update to 2.0.4 (bugfix + Basic PHP 5.3 support)

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Oct 09 2008 Christopher Stone <chris.stone@gmail.com> 2.0.3-4
- Add code coverage patch (bz #460348)
- http://bugs.xdebug.org/bug_view_page.php?bug_id=0000344

* Thu Oct 09 2008 Christopher Stone <chris.stone@gmail.com> 2.0.3-3
- Revert last change

* Thu Oct 09 2008 Christopher Stone <chris.stone@gmail.com> 2.0.3-2
- Add php-xml to Requires (bz #464758)

* Thu May 22 2008 Christopher Stone <chris.stone@gmail.com> 2.0.3-1
- Upstream sync
- Clean up libedit usage
- Minor rpmlint fix

* Sun Mar 02 2008 Christopher Stone <chris.stone@gmail.com> 2.0.2-4
- Add %%{__pecl} to post/postun Requires

* Fri Feb 22 2008 Christopher Stone <chris.stone@gmail.com> 2.0.2-3
- %%define %%pecl_name to properly register package
- Install xml package description
- Add debugclient
- Many thanks to Edward Rudd (eddie@omegaware.com) (bz #432681)

* Wed Feb 20 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 2.0.2-2
- Autorebuild for GCC 4.3

* Sun Nov 25 2007 Christopher Stone <chris.stone@gmail.com> 2.0.2-1
- Upstream sync

* Sun Sep 30 2007 Christopher Stone <chris.stone@gmail.com> 2.0.0-2
- Update to latest standards
- Fix encoding on Changelog

* Sat Sep 08 2007 Christopher Stone <chris.stone@gmail.com> 2.0.0-1
- Upstream sync
- Remove %%{?beta} tags

* Sun Mar 11 2007 Christopher Stone <chris.stone@gmail.com> 2.0.0-0.5.RC2
- Create directory to untar sources
- Use new ABI check for FC6
- Remove %%{release} from Provides

* Mon Jan 29 2007 Christopher Stone <chris.stone@gmail.com> 2.0.0-0.4.RC2
- Compile with $RPM_OPT_FLAGS
- Use $RPM_BUILD_ROOT instead of %%{buildroot}
- Fix license tag

* Mon Jan 15 2007 Christopher Stone <chris.stone@gmail.com> 2.0.0-0.3.RC2
- Upstream sync

* Sun Oct 29 2006 Christopher Stone <chris.stone@gmail.com> 2.0.0-0.2.RC1
- Upstream sync

* Wed Sep 06 2006 Christopher Stone <chris.stone@gmail.com> 2.0.0-0.1.beta6
- Remove Provides php-xdebug
- Fix Release
- Remove prior changelog due to Release number change
