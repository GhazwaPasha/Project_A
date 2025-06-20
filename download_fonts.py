"""
Download popular developer fonts and save them as native assets
"""
import requests
import os
from pathlib import Path

def download_file(url, filename, fonts_dir):
    """Download a file from URL and save it to fonts directory"""
    try:
        print(f"Downloading {filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        file_path = os.path.join(fonts_dir, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded {filename} ({os.path.getsize(file_path) // 1024} KB)")
        return True
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
        return False

def main():
    # Create fonts directory
    fonts_dir = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
    os.makedirs(fonts_dir, exist_ok=True)
    
    print(f"📁 Fonts will be saved to: {fonts_dir}")
    
    # Font URLs (from official sources)
    fonts_to_download = [
        # Cascadia Code from Microsoft GitHub
        {
            "url": "https://github.com/microsoft/cascadia-code/releases/download/v2111.01/CascadiaCode-2111.01.zip",
            "is_zip": True,
            "extract_files": ["ttf/CascadiaCode.ttf", "ttf/CascadiaCodePL.ttf"]
        },
        # JetBrains Mono from JetBrains GitHub
        {
            "url": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
            "is_zip": True,
            "extract_files": ["fonts/ttf/JetBrainsMono-Regular.ttf", "fonts/ttf/JetBrainsMono-Bold.ttf", "fonts/ttf/JetBrainsMono-Light.ttf", "fonts/ttf/JetBrainsMonoNL-Medium.ttf"]
        },
        # Roboto from Google Fonts
        {
            "url": "https://fonts.google.com/download?family=Roboto",
            "is_zip": True,
            "extract_files": ["static/Roboto-Regular.ttf", "static/Roboto-Bold.ttf", "static/Roboto-Light.ttf", "static/Roboto-Medium.ttf"]
        },
        # Liberation Fonts (open-source alternatives to Times New Roman and Arial/Helvetica)
        {
            "url": "https://github.com/liberationfonts/liberation-fonts/files/2926169/liberation-fonts-ttf-2.1.0.tar.gz",
            "is_zip": False,
            "is_tar": True,
            "extract_files": ["liberation-fonts-ttf-2.1.0/LiberationSerif-Regular.ttf", "liberation-fonts-ttf-2.1.0/LiberationSerif-Bold.ttf", "liberation-fonts-ttf-2.1.0/LiberationSans-Regular.ttf", "liberation-fonts-ttf-2.1.0/LiberationSans-Bold.ttf"]
        },
        # Inter (modern alternative to Helvetica)
        {
            "url": "https://github.com/rsms/inter/releases/download/v3.19/Inter-3.19.zip",
            "is_zip": True,
            "extract_files": ["Inter Desktop/Inter-Regular.ttf", "Inter Desktop/Inter-Bold.ttf", "Inter Desktop/Inter-Medium.ttf"]
        }
    ]
      import zipfile
    import tarfile
    import tempfile
    
    for font_info in fonts_to_download:
        if font_info.get("is_zip", False):
            # Download zip file
            try:
                print(f"📦 Downloading {font_info['url']}...")
                response = requests.get(font_info["url"], stream=True)
                response.raise_for_status()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_zip_path = temp_file.name
                
                # Extract specific files
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    for extract_file in font_info["extract_files"]:
                        try:
                            # Extract the file
                            zip_ref.extract(extract_file, tempfile.gettempdir())
                            
                            # Move to fonts directory with simplified name
                            extracted_path = os.path.join(tempfile.gettempdir(), extract_file)
                            final_filename = os.path.basename(extract_file)
                            final_path = os.path.join(fonts_dir, final_filename)
                            
                            # Copy file
                            import shutil
                            shutil.move(extracted_path, final_path)
                            
                            print(f"✅ Extracted {final_filename} ({os.path.getsize(final_path) // 1024} KB)")
                            
                        except Exception as e:
                            print(f"❌ Failed to extract {extract_file}: {e}")
                
                # Clean up temp file
                os.unlink(temp_zip_path)
                
            except Exception as e:
                print(f"❌ Failed to download font package: {e}")
        
        elif font_info.get("is_tar", False):
            # Download tar.gz file
            try:
                print(f"📦 Downloading {font_info['url']}...")
                response = requests.get(font_info["url"], stream=True)
                response.raise_for_status()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    temp_tar_path = temp_file.name
                
                # Extract specific files
                with tarfile.open(temp_tar_path, 'r:gz') as tar_ref:
                    for extract_file in font_info["extract_files"]:
                        try:
                            # Extract the file
                            tar_ref.extract(extract_file, tempfile.gettempdir())
                            
                            # Move to fonts directory with simplified name
                            extracted_path = os.path.join(tempfile.gettempdir(), extract_file)
                            final_filename = os.path.basename(extract_file)
                            final_path = os.path.join(fonts_dir, final_filename)
                            
                            # Copy file
                            import shutil
                            shutil.move(extracted_path, final_path)
                            
                            print(f"✅ Extracted {final_filename} ({os.path.getsize(final_path) // 1024} KB)")
                            
                        except Exception as e:
                            print(f"❌ Failed to extract {extract_file}: {e}")
                
                # Clean up temp file
                os.unlink(temp_tar_path)
                
            except Exception as e:
                print(f"❌ Failed to download font package: {e}")
                            final_path = os.path.join(fonts_dir, final_filename)
                            
                            # Copy file
                            import shutil
                            shutil.move(extracted_path, final_path)
                            
                            print(f"✅ Extracted {final_filename} ({os.path.getsize(final_path) // 1024} KB)")
                            
                        except Exception as e:
                            print(f"❌ Failed to extract {extract_file}: {e}")
                
                # Clean up temp file
                os.unlink(temp_zip_path)
                
            except Exception as e:
                print(f"❌ Failed to download font package: {e}")
    
    print(f"\n🎉 Font download complete! Check {fonts_dir}")
    
    # List downloaded fonts
    font_files = [f for f in os.listdir(fonts_dir) if f.endswith(('.ttf', '.otf'))]
    if font_files:
        print("\n📋 Downloaded fonts:")
        for font_file in font_files:
            file_path = os.path.join(fonts_dir, font_file)
            size_kb = os.path.getsize(file_path) // 1024
            print(f"  • {font_file} ({size_kb} KB)")
    else:
        print("\n⚠️  No font files found!")

if __name__ == "__main__":
    main()
