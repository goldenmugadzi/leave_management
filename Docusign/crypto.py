"""
Core Cryptography Module
Handles all PKI operations including key generation, signing, and verification
"""
import os
import hashlib
from datetime import datetime, timedelta
from io import BytesIO
from typing import Tuple, Dict, Optional

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.utils import timezone

import pyhanko
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers, fields
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.signers.pdf_signer import PdfSignatureMetadata

from PyPDF2 import PdfReader, PdfWriter


class CryptographyService:
    """
    Main cryptography service for PKI operations
    """
    
    def __init__(self):
        self.key_size = getattr(settings, 'PKI_SETTINGS', {}).get('KEY_SIZE', 2048)
        self.hash_algorithm_name = getattr(settings, 'PKI_SETTINGS', {}).get('HASH_ALGORITHM', 'SHA256')
        self.hash_algorithm = self._get_hash_algorithm(self.hash_algorithm_name)
        
    def _get_hash_algorithm(self, name: str):
        """Get cryptography hash algorithm by name"""
        algorithms = {
            'SHA256': hashes.SHA256(),
            'SHA384': hashes.SHA384(),
            'SHA512': hashes.SHA512(),
        }
        return algorithms.get(name, hashes.SHA256())
    
    def decrypt_pdf_if_needed(self, pdf_content: bytes) -> bytes:
        """
        Decrypt PDF if it's encrypted. Returns unencrypted PDF content.
        Use this when uploading/storing documents to ensure they're never encrypted in storage.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from PyPDF2 import PdfReader as PyPDF2Reader, PdfWriter as PyPDF2Writer
            
            reader = PyPDF2Reader(BytesIO(pdf_content))
            
            if reader.is_encrypted:
                logger.info("PDF is encrypted, decrypting...")
                success = reader.decrypt('')
                
                if success == 0:
                    logger.warning("Could not decrypt PDF with empty password, returning as-is")
                    return pdf_content
                
                # Re-write without encryption
                writer = PyPDF2Writer()
                for page in reader.pages:
                    writer.add_page(page)
                
                buffer = BytesIO()
                writer.write(buffer)
                buffer.seek(0)
                decrypted_content = buffer.read()
                logger.info("PDF successfully decrypted")
                return decrypted_content
            else:
                logger.debug("PDF is not encrypted")
                return pdf_content
                
        except Exception as e:
            logger.error(f"Error checking/decrypting PDF: {e}")
            return pdf_content
    
    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair
        Returns: (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size
        )
        
        # Serialize private key
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_key_pem, public_key_pem
    
    def generate_certificate(
        self,
        private_key_pem: bytes,
        subject_name: str,
        email: str,
        issuer_name: Optional[str] = None,
        issuer_private_key_pem: Optional[bytes] = None,
        validity_days: int = 365 * 5
    ) -> Tuple[bytes, str, datetime, datetime]:
        """
        Generate X.509 certificate
        Returns: (certificate_pem, serial_number, valid_from, valid_until)
        """
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        
        # Load issuer private key (self-signed if not provided)
        if issuer_private_key_pem:
            issuer_private_key = serialization.load_pem_private_key(
                issuer_private_key_pem,
                password=None
            )
        else:
            issuer_private_key = private_key
            issuer_name = subject_name
        
        # Subject and issuer
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PKI Document Signing"),
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
        ])
        
        issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PKI Document Signing"),
            x509.NameAttribute(NameOID.COMMON_NAME, issuer_name or subject_name),
        ])
        
        # Generate certificate
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=validity_days)
        
        cert_builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(valid_from)
            .not_valid_after(valid_until)
            .add_extension(
                x509.SubjectAlternativeName([x509.RFC822Name(email)]),
                critical=False,
            )
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
        )
        
        # Sign certificate
        certificate = cert_builder.sign(issuer_private_key, self.hash_algorithm)
        
        # Serialize certificate
        certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)
        serial_number = format(certificate.serial_number, 'x')
        
        return certificate_pem, serial_number, valid_from, valid_until
    
    def calculate_file_hash(self, file_content: bytes, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of file content
        """
        if algorithm == 'sha256':
            return hashlib.sha256(file_content).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(file_content).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    def sign_pdf_document(
        self,
        pdf_content: bytes,
        private_key_pem: bytes,
        certificate_pem: bytes,
        signature_reason: str = "Document Approval",
        signature_location: str = "Digital",
        visual_signature: Optional[bytes] = None,
        signature_position: Optional[Dict] = None
    ) -> bytes:
        """
        Apply digital signature to PDF document with DocMDP protection
        Returns: Signed PDF content
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if PDF is encrypted and decrypt it if necessary
        try:
            from PyPDF2 import PdfReader as PyPDF2Reader, PdfWriter as PyPDF2Writer
            
            # Try to read with PyPDF2 first to check encryption
            temp_reader = PyPDF2Reader(BytesIO(pdf_content))
            
            if temp_reader.is_encrypted:
                logger.warning("PDF is encrypted. Attempting to decrypt...")
                
                # Try empty password first (common for owner-password-only PDFs)
                success = temp_reader.decrypt('')
                
                if success == 0:
                    logger.error("Failed to decrypt PDF with empty password")
                    raise ValueError("PDF is password-protected. Please provide an unencrypted PDF for signing.")
                
                logger.info(f"Successfully decrypted PDF (result code: {success})")
                
                # Re-write PDF without encryption
                writer = PyPDF2Writer()
                for page_num in range(len(temp_reader.pages)):
                    writer.add_page(temp_reader.pages[page_num])
                
                # Write to buffer
                decrypted_buffer = BytesIO()
                writer.write(decrypted_buffer)
                decrypted_buffer.seek(0)
                pdf_content = decrypted_buffer.read()
                logger.info("PDF successfully decrypted and re-written without encryption")
            else:
                logger.info("PDF is not encrypted, proceeding with signing")
                
        except Exception as decrypt_err:
            logger.error(f"Error during PDF decryption check: {decrypt_err}", exc_info=True)
            # If decryption fails, we'll try to proceed anyway
            # The IncrementalPdfFileWriter might handle it
        
        # Now create the pyhanko reader with decrypted content
        pdf_buffer = BytesIO(pdf_content)
        pdf_reader = PdfFileReader(pdf_buffer)
        
        # Load private key and certificate using cryptography
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from cryptography import x509 as crypto_x509
        from pyhanko.sign.signers import SimpleSigner
        from pyhanko.sign.signers.pdf_signer import PdfSignatureMetadata as SigMeta
        
        # Load the key and certificate
        signing_key = load_pem_private_key(private_key_pem, password=None)
        signing_cert = crypto_x509.load_pem_x509_certificate(certificate_pem)
        
        # Convert cryptography objects to asn1crypto format for pyhanko
        from cryptography.hazmat.primitives import serialization as crypto_serialization
        from asn1crypto import x509 as asn1_x509
        from asn1crypto import keys as asn1_keys
        
        # Convert certificate to DER then to asn1crypto format
        cert_der = signing_cert.public_bytes(crypto_serialization.Encoding.DER)
        signing_cert_asn1 = asn1_x509.Certificate.load(cert_der)
        
        # Convert private key to DER then to asn1crypto format
        key_der = signing_key.private_bytes(
            encoding=crypto_serialization.Encoding.DER,
            format=crypto_serialization.PrivateFormat.PKCS8,
            encryption_algorithm=crypto_serialization.NoEncryption()
        )
        signing_key_asn1 = asn1_keys.PrivateKeyInfo.load(key_der)
        
        # Create a certificate registry with the asn1crypto certificate
        from pyhanko.sign.signers.pdf_cms import SimpleCertificateStore
        cert_registry = SimpleCertificateStore()
        cert_registry.register(signing_cert_asn1)
        
        # Create SimpleSigner with asn1crypto objects
        from pyhanko.sign import signers as sign_module
        signer = sign_module.SimpleSigner(
            signing_cert=signing_cert_asn1,
            signing_key=signing_key_asn1,
            cert_registry=cert_registry
        )
        
        # Create signature metadata with unique field name
        import uuid
        field_name = f'Signature_{uuid.uuid4().hex[:8]}'
        signature_meta = PdfSignatureMetadata(
            field_name=field_name,
            reason=signature_reason,
            location=signature_location,
            certify=False,  # Don't certify to allow multiple signatures
            # Don't set any DocMDP permissions to allow unlimited signatures
            subfilter=fields.SigSeedSubFilter.ADOBE_PKCS7_DETACHED,  # Use standard subfilter for compatibility
        )
        
        # Prepare output buffer
        output_buffer = BytesIO()
        
        # Sign the PDF. If a visual signature image was provided, create a
        # stamp style that uses the image as the background so transparency
        # is preserved when the signature appearance is rendered.
        # Enable strict=False to allow hybrid xref sections
        # For incremental signing (multiple signatures), we need to ensure we're not modifying existing content
        try:
            writer = IncrementalPdfFileWriter(pdf_buffer, strict=False)
        except Exception as e:
            # If incremental writer fails, it might be due to existing restrictions
            # Try to create a fresh PDF writer by reading and rewriting
            raise ValueError(f"Cannot create incremental writer. Document may have signing restrictions: {str(e)}")
        
        # Check if document already has signatures with DocMDP restrictions
        try:
            existing_sigs = list(fields.enumerate_sig_fields(writer))
            if existing_sigs:
                # Document already has signatures - check for DocMDP restrictions
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Document has {len(existing_sigs)} existing signature(s), adding incremental signature")
                
                # Try to detect if existing signatures have restrictions
                try:
                    from pyhanko.sign.validation import validate_pdf_signature
                    # Check the first signature for DocMDP
                    first_sig = writer.prev.root.get('/AcroForm', {}).get('/Fields', [])[0]
                    if first_sig:
                        logger.info("Checking first signature for DocMDP restrictions")
                except Exception as check_err:
                    logger.warning(f"Could not check for DocMDP restrictions: {check_err}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not enumerate existing signatures: {e}")
        
        # Add signature field with unique name
        # Extract page number from signature_position (0-based index)
        page_num = signature_position.get('page', 0) if signature_position else 0
        
        fields.append_signature_field(
            writer,
            sig_field_spec=fields.SigFieldSpec(
                sig_field_name=field_name,
                on_page=page_num,
                box=(10, 10, 200, 60) if not signature_position else (
                    signature_position.get('x', 10),
                    signature_position.get('y', 10),
                    signature_position.get('x', 10) + signature_position.get('width', 190),
                    signature_position.get('y', 10) + signature_position.get('height', 50)
                )
            )
        )

        if visual_signature:
            try:
                from PIL import Image
                from pyhanko.pdf_utils.images import PdfImage
                from pyhanko.stamp.static import StaticStampStyle

                img = Image.open(BytesIO(visual_signature))
                # Ensure image has an alpha channel so transparency is preserved
                try:
                    img = img.convert('RGBA')
                except Exception:
                    img = img.convert('RGB')
                pdf_img = PdfImage(img, writer=None)
                # Use a static stamp style whose background is the image and
                # remove the default border so only the transparent image is visible.
                stamp_style = StaticStampStyle(
                    background=pdf_img,
                    background_opacity=1.0,
                    border_width=0,
                )

                pdf_signer = signers.PdfSigner(
                    signature_meta, signer, stamp_style=stamp_style
                )
                # Use the PdfSigner instance to sign so the appearance
                # rendering will include our image background (preserving alpha).
                pdf_signer.sign_pdf(writer, output=output_buffer)
            except Exception:
                # Fallback to default signing if anything goes wrong
                signers.sign_pdf(
                    writer,
                    signature_meta=signature_meta,
                    signer=signer,
                    output=output_buffer,
                )
        else:
            # No visual image provided; do the usual signing flow
            signers.sign_pdf(
                writer,
                signature_meta=signature_meta,
                signer=signer,
                output=output_buffer,
            )
        
        return output_buffer.getvalue()
    
    def verify_pdf_signature(self, pdf_content: bytes) -> Dict:
        """
        Verify digital signature on PDF document
        Returns: Verification result dictionary
        """
        try:
            pdf_buffer = BytesIO(pdf_content)
            reader = PdfFileReader(pdf_buffer)
            
            # Get embedded signatures
            sig_fields = fields.enumerate_sig_fields(reader)
            
            if not sig_fields:
                return {
                    'valid': False,
                    'error': 'No signatures found in document',
                    'details': {}
                }
            
            results = []
            for sig_field in sig_fields:
                try:
                    # Validate signature
                    validation_result = validate_pdf_signature(
                        reader.get_signature_field(sig_field.field_name)
                    )
                    
                    results.append({
                        'field_name': sig_field.field_name,
                        'valid': validation_result.bottom_line,
                        'intact': validation_result.intact,
                        'trusted': validation_result.trusted,
                        'signer_info': {
                            'name': validation_result.signer_info.get('name', 'Unknown'),
                            'timestamp': str(validation_result.timestamp) if hasattr(validation_result, 'timestamp') else None,
                        }
                    })
                except Exception as e:
                    results.append({
                        'field_name': sig_field.field_name,
                        'valid': False,
                        'error': str(e)
                    })
            
            # Overall verification result
            all_valid = all(r.get('valid', False) for r in results)
            
            return {
                'valid': all_valid,
                'signatures': results,
                'signature_count': len(results)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Verification failed: {str(e)}',
                'details': {}
            }
    
    def encrypt_private_key(self, private_key_pem: bytes, password: str) -> bytes:
        """
        Encrypt private key with password
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        
        encrypted_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
        )
        
        return encrypted_key
    
    def decrypt_private_key(self, encrypted_key_pem: bytes, password: str) -> bytes:
        """
        Decrypt private key with password
        """
        private_key = serialization.load_pem_private_key(
            encrypted_key_pem,
            password=password.encode()
        )
        
        decrypted_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return decrypted_key
    
    def create_signature_data(
        self,
        data: bytes,
        private_key_pem: bytes
    ) -> bytes:
        """
        Create digital signature for arbitrary data
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None
        )
        
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(self.hash_algorithm),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            self.hash_algorithm
        )
        
        return signature
    
    def verify_signature_data(
        self,
        data: bytes,
        signature: bytes,
        public_key_pem: bytes
    ) -> bool:
        """
        Verify digital signature for arbitrary data
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem
            )
            
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(self.hash_algorithm),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                self.hash_algorithm
            )
            return True
        except Exception:
            return False
    
    def add_visual_signature_to_pdf(
        self,
        pdf_content: bytes,
        visual_signature: bytes,
        signature_position: Dict
    ) -> bytes:
        """
        Add visual signature image to PDF without cryptographic signing
        This is for approval/acknowledgment purposes only (not legally binding digital signature)
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from PyPDF2 import PdfReader, PdfWriter
        
        # Load the original PDF
        pdf_buffer = BytesIO(pdf_content)
        reader = PdfReader(pdf_buffer)
        writer = PdfWriter()
        
        # Get position details
        page_num = signature_position.get('page', 0)
        x = signature_position.get('x', 100)
        y = signature_position.get('y', 700)
        width = signature_position.get('width', 150)
        height = signature_position.get('height', 50)
        
        # Create signature overlay
        overlay_buffer = BytesIO()
        page_size = reader.pages[page_num].mediabox
        page_width = float(page_size.width)
        page_height = float(page_size.height)
        
        # Create canvas for overlay
        c = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
        
        # Add signature image
        img_reader = ImageReader(BytesIO(visual_signature))
        c.drawImage(img_reader, x, y, width=width, height=height, mask='auto')
        c.save()
        
        # Merge overlay with original page
        overlay_buffer.seek(0)
        overlay_reader = PdfReader(overlay_buffer)
        
        # Copy all pages and merge signature on target page
        for i, page in enumerate(reader.pages):
            if i == page_num:
                page.merge_page(overlay_reader.pages[0])
            writer.add_page(page)
        
        # Write result to buffer
        result_buffer = BytesIO()
        writer.write(result_buffer)
        result_buffer.seek(0)
        
        return result_buffer.read()


# Singleton instance
crypto_service = CryptographyService()
