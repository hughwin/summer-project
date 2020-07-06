import subprocess


def main():
    subprocess.call("python pix2pix/pix2pix.py --mode test --input_dir pix2pix/val --output_dir pix2pix/test "
                    "--checkpoint "
                    "pix2pix/checkpoint")


if __name__ == "__main__":
    main()
