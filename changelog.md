# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.2] - 2025-11-07

### Fixed

- Emails without a DAWA address are now properly skipped.

## [2.1.1] - 2025-10-30

### Changed

- Specified zero debt info in result mail.

### Fixed

- Only read names from first "ul" list in mail body.

## [2.1.0] - 2025-10-24

### Changed

- Added date to tax data in result email.
- Only look for cases under "02 Ejendom" in SAP.
- Removed duplicates of missing payments from SAP.
- Tax data is checked for the current year instead of the latest available.

### Fixed

- Minor typos and rewording of result email.
- Bug when no tax data was available in Structura.
- Properties which are "Udgået" are now skipped.
- Fixed regex error when an address has a space in the city name.

## [2.0.1] - 2025-10-07

### Fixed

- Values unpacking in email template.
- Re-added missing go case id to email subject.

## [2.0.0] - 2025-10-02

### Added

- Added Doc2Archive process.

### Changed

- Changed email logic to new OS2Forms output.
- Added pretty template to result email.
- Added skip when frozen debt has been sent to SAP within 3 days.

### Fixed

- Skip cases where address is not in Structura.

## [1.4.0] - 2025-06-10

### Changed

- Added date to GO documents titles.
- Reversed order of tasks to take oldest first.
- Upped allowed error count and don't pause trigger on too many errors.

## [1.3.0] - 2025-05-01

### Changed

- Search for existing case in GO before creating a new one.

## [1.2.2] - 2025-04-24

### Fixed

- Added wait for KMD Logon screen.

## [1.2.1] - 2025-04-16

### Fixed

- Address match should provide better results.

## [1.2.0] - 2025-04-03

### Changed

- Now includes released frozen debt in result.
- Tax data is included in result.

## [1.1.0] - 2025-03-26

### Changed

- Using difflib to compare owner names.

## [1.0.0] - 2025-02-13

- Initial release

[2.1.2]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/2.1.2
[2.1.1]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/2.1.1
[2.1.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/2.1.0
[2.0.1]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/2.0.1
[2.0.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/2.0.0
[1.4.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.4.0
[1.3.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.3.0
[1.2.2]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.2.2
[1.2.1]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.2.1
[1.2.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.2.0
[1.1.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.1.0
[1.0.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.0.0
