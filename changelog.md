# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[2.0.1]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/2.0.1
[2.0.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/2.0.0
[1.4.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.4.0
[1.3.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.3.0
[1.2.2]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.2.2
[1.2.1]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.2.1
[1.2.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.2.0
[1.1.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.1.0
[1.0.0]: https://github.com/itk-dev-rpa/Forespoergsler-til-Ejendomsbeskatningen/releases/tag/1.0.0
