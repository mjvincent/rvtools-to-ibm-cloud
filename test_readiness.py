from logic_engine import assess_image_readiness


def test_ready_linux_vm():
    result = assess_image_readiness(
        "Red Hat Enterprise Linux 8 (64-bit)",
        "efi",
        80,
        1,
        "poweredOn"
    )
    assert result["status"] == "Ready"
    assert result["guest_customization"] == "cloud-init required"


def test_blocked_oversized_boot_disk():
    result = assess_image_readiness(
        "Microsoft Windows Server 2022 (64-bit)",
        "bios",
        300,
        1,
        "poweredOn"
    )
    assert result["status"] == "Blocked"
    assert "250 GB" in result["reasons"]
    assert result["guest_customization"] == "cloudbase-init required"


def test_review_multi_disk_unknown_os():
    result = assess_image_readiness(
        "",
        "",
        8,
        2,
        "poweredOff"
    )
    assert result["status"] == "Review"
    assert "Guest OS missing" in result["reasons"]
    assert "Multiple disks" in result["reasons"]


if __name__ == "__main__":
    test_ready_linux_vm()
    test_blocked_oversized_boot_disk()
    test_review_multi_disk_unknown_os()
    print("image readiness tests ok")
