import os

import pytest


@pytest.fixture(scope="function")
def unbreakable_kernel(shell):
    """
    Fixture.
    Install unbreakable kernel and reboot using the tmt-reboot.
    After the test boot back to the supported kernel.
    """
    if os.environ["TMT_REBOOT_COUNT"] == "0":
        assert shell("yum install -y kernel-uek").returncode == 0
        kernel_version = shell("rpm -q --last kernel-uek | head -1 | cut -d ' ' -f1 | sed 's/kernel-uek-//'").output
        assert shell(f"grubby --set-default /boot/vmlinuz-{kernel_version}").returncode == 0
        shell("tmt-reboot -t 600")

    yield

    if os.environ["TMT_REBOOT_COUNT"] == "1":
        shell(
            "grubby --set-default /boot/vmlinuz-`rpm -q --qf '%{BUILDTIME}\t%{EVR}.%{ARCH}\n' kernel | sort -nr | head -1 | cut -f2`"
        )
        shell("tmt-reboot -t 600")


@pytest.mark.test_unsupported_unbreakable_enterprise_kernel
def test_bad_conversion(shell, convert2rhel):
    """
    Verify that the check for compatible kernel on Oracle Linux works.
    Install unsupported kernel and run the conversion.
    Expect the RHEL_COMPATIBLE_KERNEL.BOOTED_KERNEL_INCOMPATIBLE warning message and terminate the utility.
    """
    if os.environ["TMT_REBOOT_COUNT"] == "1":
        with convert2rhel("-y --debug", unregister=True) as c2r:
            c2r.expect(
                "RHEL_COMPATIBLE_KERNEL::INCOMPATIBLE_VERSION - Incompatible booted kernel version",
                timeout=600,
            )
            c2r.sendcontrol("c")

            assert c2r.exitstatus != 0
