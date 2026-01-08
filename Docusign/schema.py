"""
GraphQL Schema for Documents
"""
import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
import base64
from io import BytesIO

from .models import Document, Signature, Request, PossibleSigner, Sign, Initial, AuditLog
from .crypto import crypto_service
import logging

User = get_user_model()


class DocumentType(DjangoObjectType):
    """GraphQL Type for Document"""
    signing_requests = graphene.List(lambda: RequestType)
    
    class Meta:
        model = Document
        fields = '__all__'
    
    def resolve_signing_requests(self, info):
        return self.reqs.all()


class SignatureType(DjangoObjectType):
    """GraphQL Type for Signature"""
    class Meta:
        model = Signature
        fields = '__all__'


class RequestType(DjangoObjectType):
    """GraphQL Type for Request"""
    class Meta:
        model = Request
        fields = '__all__'


class PossibleSignerType(DjangoObjectType):
    """GraphQL Type for PossibleSigner"""
    class Meta:
        model = PossibleSigner
        fields = '__all__'


class SignType(DjangoObjectType):
    """GraphQL Type for Sign"""
    class Meta:
        model = Sign
        fields = '__all__'


class InitialType(DjangoObjectType):
    """GraphQL Type for Initial"""
    class Meta:
        model = Initial
        fields = '__all__'


# Note: `UploadDocument` is implemented further down; the earlier incomplete
# implementation was removed to fix a SyntaxError caused by an unclosed try
# block. The full, working `UploadDocument` mutation appears later in this file.

class CreateSignature(graphene.Mutation):
    """Create a signature template"""
    class Arguments:
        image = Upload(required=False)
        text = graphene.String(required=False)
        font = graphene.String(required=False)
        requires_pki = graphene.Boolean(required=False)
        description = graphene.String(required=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    signature = graphene.Field(SignatureType)
    
    @staticmethod
    def mutate(root, info, image=None, text=None, font=None, requires_pki=False, description=None):
        user = info.context.user
        if not user.is_authenticated:
            return CreateSignature(
                success=False,
                message="Authentication required",
                signature=None
            )
        
        try:
            logging.getLogger('apps.documents').info(
                f"CreateSignature called by user={getattr(user, 'id', None)} image={bool(image)} text_provided={bool(text)} font={font}"
            )
            signature = None
            
            if image:
                # Handle uploaded image signature
                try:
                    from PIL import Image
                    from django.core.files.base import ContentFile
                    # Read uploaded bytes and open with Pillow
                    uploaded_bytes = image.read()
                    img = Image.open(BytesIO(uploaded_bytes))
                    # Ensure RGBA for transparency
                    try:
                        img = img.convert('RGBA')
                    except Exception:
                        img = img.convert('RGB')

                    # Make white / near-white background pixels transparent
                    try:
                        datas = img.getdata()
                        new_data = []
                        # threshold for "near white" pixels
                        THRESH = 250
                        for item in datas:
                            # item can be RGBA or RGB
                            if len(item) >= 3:
                                r, g, b = item[0], item[1], item[2]
                                a = item[3] if len(item) == 4 else 255
                                if a == 0:
                                    new_data.append((r, g, b, a))
                                    continue
                                # if pixel is near-white, make transparent
                                if r >= THRESH and g >= THRESH and b >= THRESH:
                                    new_data.append((255, 255, 255, 0))
                                else:
                                    new_data.append((r, g, b, a))
                            else:
                                new_data.append(item)
                        img.putdata(new_data)
                    except Exception:
                        # If per-pixel manipulation fails, continue with RGBA image
                        logging.getLogger('apps.documents').debug('Failed to apply white->transparent mask; saving RGBA image')

                    # Save processed image to an in-memory file and attach to model
                    out = BytesIO()
                    img.save(out, format='PNG')
                    out.seek(0)
                    file_name = getattr(image, 'name', 'signature.png')
                    # normalize extension to .png
                    if not file_name.lower().endswith('.png'):
                        file_name = file_name.rsplit('.', 1)[0] + '.png'

                    signature = Signature.objects.create(owner=user, requires_pki=requires_pki, description=description)
                    signature.image.save(file_name, ContentFile(out.read()), save=True)
                    signature.refresh_from_db()

                    try:
                        img_name = signature.image.name if signature.image else None
                        img_url = signature.image.url if signature.image else None
                        logging.getLogger('apps.documents').info(
                            f"Saved signature image: name={img_name} url={img_url}"
                        )
                    except Exception:
                        logging.getLogger('apps.documents').exception('Could not read saved image url')
                except Exception:
                    # Fallback: save the uploaded file directly if processing fails
                    logging.getLogger('apps.documents').exception('Failed processing uploaded signature image; saving raw upload')
                    signature = Signature.objects.create(owner=user, image=image, requires_pki=requires_pki, description=description)
            elif text and font:
                # Handle text-based signature
                # For now, we'll store it without generating an image
                # In production, you'd want to generate an image from the text+font
                signature = Signature.objects.create(
                    owner=user,
                    requires_pki=requires_pki,
                    description=description
                )
            else:
                return CreateSignature(
                    success=False,
                    message="Either image or (text and font) must be provided",
                    signature=None
                )
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='create_signature',
                details={
                    'signature_id': str(signature.id),
                    'type': 'image' if image else 'text'
                }
            )

            # Extra debug log to help troubleshooting why signatures may not appear
            logging.getLogger('apps.documents').info(
                f"Signature created: id={signature.id}, owner={getattr(signature.owner, 'id', None)}, has_image={bool(getattr(signature, 'image', None))}"
            )
            
            return CreateSignature(
                success=True,
                message="Signature created successfully",
                signature=signature
            )
            
        except Exception as e:
            logging.getLogger('apps.documents').exception('CreateSignature failed')
            return CreateSignature(
                success=False,
                message=f"Failed to create signature: {str(e)}",
                signature=None
            )


class UploadDocument(graphene.Mutation):
    """Upload a PDF document"""
    class Arguments:
        title = graphene.String(required=True)
        file = Upload(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    document = graphene.Field(DocumentType)
    
    @staticmethod
    def mutate(root, info, title, file):
        user = info.context.user
        if not user.is_authenticated:
            return UploadDocument(
                success=False,
                message="Authentication required",
                document=None
            )
        
        try:
            # Handle file object - graphene-file-upload passes the file directly
            uploaded_file = file
            
            # Check if it's a valid file object
            if not hasattr(uploaded_file, 'read'):
                return UploadDocument(
                    success=False,
                    message=f"Invalid file object: {type(uploaded_file)}",
                    document=None
                )
            
            # Read file content
            file_content = uploaded_file.read()
            file_name = getattr(uploaded_file, 'name', 'document.pdf')
            
            # Validate PDF
            if not file_name.lower().endswith('.pdf'):
                return UploadDocument(
                    success=False,
                    message="Only PDF files are allowed",
                    document=None
                )
            
            # Decrypt PDF if encrypted (store unencrypted, encrypt only on download)
            crypto_service = CryptographyService()
            decrypted_content = crypto_service.decrypt_pdf_if_needed(file_content)
            
            # Create document with decrypted content
            from django.core.files.base import ContentFile
            document = Document.objects.create(
                title=title,
                file=ContentFile(decrypted_content, name=file_name),
                uploaded_by=user
            )
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='upload',
                details={
                    'document_id': str(document.id),
                    'title': title
                }
            )
            
            return UploadDocument(
                success=True,
                message="Document uploaded successfully",
                document=document
            )
            
        except Exception as e:
            return UploadDocument(
                success=False,
                message=f"Upload failed: {str(e)}",
                document=None
            )


class SignerPositionInput(graphene.InputObjectType):
    """Input type for signer position"""
    # The app no longer stores visual position fields on PossibleSigner.
    # Keep user_id and allow an optional role (signer/verifier/reviewer/approver).
    user_id = graphene.ID(required=True)
    role = graphene.String(default_value='signer')


class CreateSigningRequest(graphene.Mutation):
    """Create a signing request with multiple signers and their positions"""
    class Arguments:
        document_id = graphene.ID(required=True)
        signers = graphene.List(SignerPositionInput, required=True)
        require_all_signatures = graphene.Boolean(required=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    request = graphene.Field(RequestType)
    
    @staticmethod
    def mutate(root, info, document_id, signers, require_all_signatures=False):
        user = info.context.user
        if not user.is_authenticated:
            return CreateSigningRequest(
                success=False,
                message="Authentication required",
                request=None
            )
        
        try:
            document = Document.objects.get(id=document_id)
            
            # Check if user already has existing requests for this document
            existing_requests = Request.objects.filter(
                document=document,
                requester=user
            )
            
            if existing_requests.exists():
                # Delete only unsigned requests and their possible signers
                for req in existing_requests:
                    if not req.signs.exists():  # Only delete if no signatures
                        req.poss_signers.all().delete()
                        req.delete()
            
            # Create signing request
            signing_request = Request.objects.create(
                document=document,
                requester=user,
                status='pending'
            )
            
            # Add signers with their positions
            for signer_data in signers:
                # signer_data may be a dict (from variables) or an object-like input
                if isinstance(signer_data, dict):
                    user_id = signer_data.get('userId') or signer_data.get('user_id')
                    role_val = signer_data.get('role')
                else:
                    user_id = getattr(signer_data, 'user_id', None) or getattr(signer_data, 'userId', None)
                    role_val = getattr(signer_data, 'role', None)

                if not user_id:
                    raise ValueError('Signer entry missing user id')

                signer_user = User.objects.get(id=user_id)

                # Create PossibleSigner without deprecated visual position fields
                PossibleSigner.objects.create(
                    request=signing_request,
                    signer=signer_user,
                    role=(role_val or 'signer')
                )
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='create_signing_request',
                details={
                    'request_id': str(signing_request.id),
                    'document_id': str(document.id),
                    'signers_count': len(signers)
                }
            )
            
            return CreateSigningRequest(
                success=True,
                message="Signing request created successfully",
                request=signing_request
            )
            
        except Document.DoesNotExist:
            return CreateSigningRequest(
                success=False,
                message="Document not found",
                request=None
            )
        except User.DoesNotExist:
            return CreateSigningRequest(
                success=False,
                message="One or more signers not found",
                request=None
            )
        except Exception as e:
            return CreateSigningRequest(
                success=False,
                message=f"Failed to create signing request: {str(e)}",
                request=None
            )


class InitialInput(graphene.InputObjectType):
    """Input type for initials placement"""
    page_number = graphene.Int(required=True)
    x_position = graphene.Float(required=True)
    y_position = graphene.Float(required=True)
    width = graphene.Float(required=True)
    height = graphene.Float(required=True)


class SignDocument(graphene.Mutation):
    """Apply digital signature to a document"""
    class Arguments:
        document_id = graphene.ID(required=True)
        signature_id = graphene.ID(description="ID of the signature template to use")
        private_key_password = graphene.String(required=False, description="Password for PKI key encryption/decryption")
        visual_signature_base64 = graphene.String(description="Base64 encoded visual signature image")
        signature_position = graphene.JSONString(description="Position: {page, x, y, width, height}")
        signature_reason = graphene.String(default_value="Document Approval")
        initials = graphene.List(InitialInput, description="List of initials to add to document")
    
    success = graphene.Boolean()
    message = graphene.String()
    signature = graphene.Field(SignatureType)
    signed_document_url = graphene.String()
    
    @staticmethod
    def mutate(root, info, document_id, private_key_password, signature_id=None,
               visual_signature_base64=None, signature_position=None,
               signature_reason="Document Approval", initials=None):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=== SignDocument mutation called ===")
        logger.info(f"Document ID: {document_id}")
        logger.info(f"Signature reason: {signature_reason}")
        logger.info(f"Has visual signature: {visual_signature_base64 is not None}")
        logger.info(f"Signature position: {signature_position}")
        logger.info(f"Signature position type: {type(signature_position)}")
        
        user = info.context.user
        if not user.is_authenticated:
            error_msg = "ERROR: Unauthenticated user attempted to sign document"
            logger.warning(error_msg)
            return SignDocument(
                success=False,
                message="Authentication required",
                signature=None,
                signed_document_url=None
            )
        logger.info(f"User: {user.username}")
        
        try:
            # Get document
            logger.info(f"Fetching document with ID: {document_id}")
            document = Document.objects.get(id=document_id)
            logger.info(f"Document found: {document.title}")
            
            # Get signature template if signature_id provided
            signature_template = None
            if signature_id:
                try:
                    signature_template = Signature.objects.get(id=signature_id, owner=user)
                    logger.info(f"Signature template found: requires_pki={signature_template.requires_pki}")
                    
                    # If signature requires PKI but has no key pair, check if password provided for generation
                    if signature_template.requires_pki:
                        if not signature_template.pki_key_pair or not signature_template.pki_key_pair.is_active:
                            # If password is provided, we can generate keys on-the-fly
                            if private_key_password:
                                logger.info("No PKI key pair assigned, but password provided - will generate keys on-the-fly")
                            else:
                                error_msg = f"ERROR: Signature template requires PKI but no active PKI key pair is assigned and no password provided"
                                logger.error(error_msg)
                                return SignDocument(
                                    success=False,
                                    message="This signature requires PKI protection but no active PKI key pair is assigned. Please provide a password to generate keys, or configure the signature with an existing PKI key pair.",
                                    signature=None,
                                    signed_document_url=None
                                )
                        else:
                            logger.info("Signature requires PKI - signature's PKI key pair will be used")
                    else:
                        logger.info("Signature does not require PKI")
                except Signature.DoesNotExist:
                    error_msg = f"ERROR: Signature template with ID {signature_id} not found for user {user.username}"
                    logger.error(error_msg)
                    return SignDocument(
                        success=False,
                        message="Signature template not found",
                        signature=None,
                        signed_document_url=None
                    )
            
            # Determine which keys to use based on signature requirements
            generate_new_keys = False
            if signature_template and signature_template.requires_pki:
                # Check if we need to generate keys on-the-fly
                if not signature_template.pki_key_pair or not signature_template.pki_key_pair.is_active:
                    if private_key_password:
                        # Generate new PKI keys on-the-fly
                        logger.info("Generating new PKI keys on-the-fly")
                        generate_new_keys = True
                        private_key_encrypted = None
                        certificate_pem = None
                    else:
                        error_msg = "ERROR: PKI keys required but signature has no active PKI key pair assigned and no password provided"
                        logger.error(error_msg)
                        return SignDocument(
                            success=False,
                            message="PKI keys required but signature has no active PKI key pair assigned.",
                            signature=None,
                            signed_document_url=None
                        )
                else:
                    # Use PKI keys from the signature's assigned PKI key pair
                    private_key_encrypted = signature_template.pki_key_pair.private_key_encrypted
                    certificate_pem = signature_template.pki_key_pair.certificate_pem
                    logger.info(f"Using signature's PKI key pair: {signature_template.pki_key_pair.name}")
            elif signature_template and not signature_template.requires_pki:
                # Signature doesn't require PKI - skip password check
                logger.info("Signature does not require PKI - skipping key decryption")
                private_key_encrypted = None
                certificate_pem = None
            else:
                # No signature template - use default behavior (backward compatibility)
                pki_key_pair = user.pki_key_pairs.filter(is_default=True, is_active=True).first()
                if pki_key_pair:
                    private_key_encrypted = pki_key_pair.private_key_encrypted
                    certificate_pem = pki_key_pair.certificate_pem
                    logger.info("Using user's default PKI keys")
                else:
                    private_key_encrypted = None
                    certificate_pem = None
                    logger.info("No PKI keys available - signature without PKI")
            
            # Generate or decrypt private key
            private_key_pem = None
            public_key_pem = None
            
            if generate_new_keys:
                # Generate new PKI keys on-the-fly
                try:
                    logger.info("Generating new RSA key pair")
                    
                    # Generate key pair
                    private_key_pem_raw, public_key_pem = crypto_service.generate_key_pair()
                    
                    # Generate self-signed certificate
                    logger.info("Generating self-signed certificate")
                    certificate_pem_raw, serial_number, valid_from, valid_until = crypto_service.generate_certificate(
                        private_key_pem=private_key_pem_raw,
                        subject_name=user.username,
                        email=user.email or f"{user.username}@example.com"
                    )
                    certificate_pem = certificate_pem_raw
                    
                    # Encrypt private key with password
                    logger.info("Encrypting private key with provided password")
                    private_key_encrypted_raw = crypto_service.encrypt_private_key(
                        private_key_pem_raw,
                        private_key_password
                    )
                    
                    # Store encrypted key for later (will be saved to signature)
                    private_key_encrypted_to_save = private_key_encrypted_raw.decode('utf-8') if isinstance(private_key_encrypted_raw, bytes) else private_key_encrypted_raw
                    public_key_pem_to_save = public_key_pem.decode('utf-8') if isinstance(public_key_pem, bytes) else public_key_pem
                    certificate_pem_to_save = certificate_pem.decode('utf-8') if isinstance(certificate_pem, bytes) else certificate_pem
                    
                    # Use the raw (unencrypted) private key for signing
                    private_key_pem = private_key_pem_raw
                    
                    logger.info("New PKI keys generated successfully")
                    
                except Exception as e:
                    error_msg = "ERROR: Failed to generate PKI keys"
                    logger.error(f"{error_msg}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return SignDocument(
                        success=False,
                        message=f"Failed to generate PKI keys: {str(e)}",
                        signature=None,
                        signed_document_url=None
                    )
            elif private_key_encrypted:
                # Decrypt existing private key
                try:
                    logger.info("Attempting to decrypt private key")
                    private_key_pem = crypto_service.decrypt_private_key(
                        private_key_encrypted.encode('utf-8'),
                        private_key_password
                    )
                    logger.info("Private key decrypted successfully")
                except Exception as e:
                    error_msg = f"ERROR: Failed to decrypt private key"
                    logger.error(f"{error_msg}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return SignDocument(
                        success=False,
                        message="Invalid private key password",
                        signature=None,
                        signed_document_url=None
                    )
            
            # Read original document
            document.file.open('rb')
            original_content = document.file.read()
            document.file.close()
            
            # Check if document already has signatures (diagnostic)
            try:
                from pyhanko.pdf_utils.reader import PdfFileReader
                from pyhanko.sign import fields as pdf_fields
                from io import BytesIO
                
                check_buffer = BytesIO(original_content)
                check_reader = PdfFileReader(check_buffer)
                existing_signatures = list(pdf_fields.enumerate_sig_fields(check_reader))
                
                logger.info(f"Document currently has {len(existing_signatures)} signature(s)")
                if existing_signatures:
                    logger.info(f"Existing signature fields: {[sig.field_name for sig in existing_signatures]}")
            except Exception as check_err:
                logger.warning(f"Could not check existing signatures: {check_err}")
            
            # Prepare optional visual signature bytes and Sign PDF
            visual_sig_bytes = None
            if visual_signature_base64:
                try:
                    logger.info(f"Decoding visual signature (length: {len(visual_signature_base64)})")
                    visual_sig_bytes = base64.b64decode(visual_signature_base64)
                    logger.info(f"Visual signature decoded successfully ({len(visual_sig_bytes)} bytes)")
                except Exception as e:
                    error_msg = f"ERROR: Failed to decode visual signature"
                    logger.error(f"{error_msg}: {str(e)}")
                    visual_sig_bytes = None

            logger.info("Calling crypto_service.sign_pdf_document")
            logger.info(f"Signature position passed to crypto: {signature_position}")
            
            # Only sign with PKI if we have the keys
            if private_key_pem and certificate_pem:
                logger.info("Signing with PKI keys")
                try:
                    signed_content = crypto_service.sign_pdf_document(
                        pdf_content=original_content,
                        private_key_pem=private_key_pem,
                        certificate_pem=certificate_pem.encode('utf-8') if isinstance(certificate_pem, str) else certificate_pem,
                        signature_reason=signature_reason,
                        signature_location="Digital Platform",
                        signature_position=signature_position,
                        visual_signature=visual_sig_bytes,
                    )
                    logger.info("PDF signed successfully with PKI")
                except Exception as sign_error:
                    error_msg = str(sign_error)
                    logger.error(f"PDF signing error: {error_msg}")
                    
                    # Check if it's a DocMDP restriction error
                    if "forbids all changes" in error_msg or "DocMDP" in error_msg or "certification signature" in error_msg:
                        logger.error(f"Document has signing restrictions: {error_msg}")
                        return SignDocument(
                            success=False,
                            message="This document has existing signature restrictions that prevent additional signatures. Please upload a new unsigned version of the document or contact the original signer to remove restrictions.",
                            signature=None,
                            signed_document_url=None
                        )
                    
                    import traceback
                    traceback.print_exc()
                    raise
            else:
                # No PKI - add visual signature without cryptographic signing
                logger.info("Adding visual signature without PKI")
                if visual_sig_bytes and signature_position:
                    try:
                        signed_content = crypto_service.add_visual_signature_to_pdf(
                            pdf_content=original_content,
                            visual_signature=visual_sig_bytes,
                            signature_position=signature_position
                        )
                        logger.info("Visual signature added successfully without PKI")
                    except Exception as e:
                        error_msg = f"Failed to add visual signature (non-PKI)"
                        logger.error(f"{error_msg}: {str(e)}")
                        # Fall back to original content if visual signature fails
                        signed_content = original_content
                else:
                    # No visual signature provided, just use original
                    signed_content = original_content

            
            # Calculate signature value only if we have PKI
            if private_key_pem:
                signature_value = crypto_service.create_signature_data(
                    original_content,
                    private_key_pem
                )
                signature_value_base64 = base64.b64encode(signature_value).decode('utf-8')
            else:
                signature_value_base64 = None
            
            # Save signed document (overwrite or create new)
            from django.core.files.base import ContentFile
            import os
            # Extract just the filename without the full path to avoid nested directories
            filename = os.path.basename(document.file.name)
            document.file.save(
                filename,
                ContentFile(signed_content),
                save=True
            )
            document.status = 'signed'
            document.save()
            
            # Find or create signing request for this document
            from .models import Request, Sign
            signing_request = Request.objects.filter(document=document).first()
            if not signing_request:
                # Create a request if it doesn't exist
                signing_request = Request.objects.create(
                    document=document,
                    requester=user,
                    status='completed'
                )
            else:
                signing_request.status = 'completed'
                signing_request.save()
            
            # Use the signature template if provided, otherwise find user's default
            if not signature_template:
                signature_template = Signature.objects.filter(owner=user).first()
            
            # If we generated new keys, save them to the signature template
            if generate_new_keys and signature_template:
                from .models import PKIKeyPair
                try:
                    logger.info("Saving generated PKI keys to new PKI key pair")
                    
                    # Create a new PKI key pair
                    pki_key_pair = PKIKeyPair.objects.create(
                        user=user,
                        name=f"Auto-generated for signature {signature_template.id}",
                        public_key_pem=public_key_pem_to_save,
                        private_key_encrypted=private_key_encrypted_to_save,
                        certificate_pem=certificate_pem_to_save,
                        is_active=True,
                        is_default=False
                    )
                    
                    # Assign it to the signature
                    signature_template.pki_key_pair = pki_key_pair
                    signature_template.requires_pki = True
                    signature_template.save()
                    
                    logger.info(f"PKI key pair created and assigned to signature: {pki_key_pair.name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to save PKI keys to signature: {str(e)}")
                    # Continue anyway - the document is already signed
            
            # Create Sign record (completed signature)
            sign_record = Sign.objects.create(
                request=signing_request,
                signer=user,
                signature=signature_template
            )
            
            # Handle visual signature if provided (save as signature template)
            if visual_signature_base64 and not signature_template:
                try:
                    visual_sig_data = base64.b64decode(visual_signature_base64)
                    from django.core.files.base import ContentFile
                    new_signature = Signature.objects.create(owner=user)
                    new_signature.image.save(
                        f'signature_{user.id}.png',
                        ContentFile(visual_sig_data),
                        save=True
                    )
                    sign_record.signature = new_signature
                    sign_record.save()
                except Exception as e:
                    pass  # Visual signature is optional
            
            # Save initials if provided
            if initials:
                logger.info(f"Saving {len(initials)} initials for user {user.username}")
                for initial_data in initials:
                    if isinstance(initial_data, dict):
                        page_num = initial_data.get('page_number') or initial_data.get('pageNumber')
                        x_pos = initial_data.get('x_position') or initial_data.get('xPosition')
                        y_pos = initial_data.get('y_position') or initial_data.get('yPosition')
                        width_val = initial_data.get('width')
                        height_val = initial_data.get('height')
                    else:
                        page_num = getattr(initial_data, 'page_number', None)
                        x_pos = getattr(initial_data, 'x_position', None)
                        y_pos = getattr(initial_data, 'y_position', None)
                        width_val = getattr(initial_data, 'width', None)
                        height_val = getattr(initial_data, 'height', None)
                    
                    Initial.objects.create(
                        user=user,
                        request=signing_request,
                        page_number=page_num,
                        x_position=x_pos,
                        y_position=y_pos,
                        width=width_val,
                        height=height_val
                    )
                logger.info(f"Successfully saved {len(initials)} initials")
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='sign',
                details={
                    'document_id': str(document.id),
                    'sign_record_id': str(sign_record.id),
                    'initials_count': len(initials) if initials else 0
                }
            )
            
            return SignDocument(
                success=True,
                message="Document signed successfully",
                signature=sign_record.signature,
                signed_document_url=document.file.url
            )
            
        except Document.DoesNotExist:
            error_msg = f"ERROR: Document not found"
            logger.error(f"{error_msg}: {document_id}")
            return SignDocument(
                success=False,
                message="Document not found",
                signature=None,
                signed_document_url=None
            )
        except Exception as e:
            logger.error(f"Signing failed with exception: {str(e)}")
            logger.exception("Full traceback:")
            import traceback
            traceback.print_exc()
            return SignDocument(
                success=False,
                message=f"Signing failed: {str(e)}",
                signature=None,
                signed_document_url=None
            )


class VerifyDocument(graphene.Mutation):
    """Verify digital signature on a document"""
    class Arguments:
        file = Upload(required=True, description="PDF file to verify")
    
    success = graphene.Boolean()
    message = graphene.String()
    result = graphene.String()
    details = graphene.JSONString()
    
    @staticmethod
    def mutate(root, info, file):
        try:
            # Read file content
            file_content = file.read()
            
            # Verify signature using crypto service
            verification_result = crypto_service.verify_pdf_signature(file_content)
            
            # Determine result status
            if verification_result.get('valid'):
                result = 'valid'
                message = "Document signature is valid and trusted"
            elif 'tampered' in verification_result.get('error', '').lower():
                result = 'invalid_tampered'
                message = "Document has been tampered with"
            elif 'certificate' in verification_result.get('error', '').lower():
                result = 'invalid_certificate'
                message = "Certificate is untrusted or invalid"
            else:
                result = 'error'
                message = verification_result.get('error', 'Verification failed')
            
            # Create audit log if user is authenticated
            if info.context.user.is_authenticated:
                AuditLog.objects.create(
                    user=info.context.user,
                    action='verify',
                    details={
                        'result': result,
                        'message': message
                    }
                )
            
            return VerifyDocument(
                success=True,
                message=message,
                result=result,
                details=verification_result
            )
            
        except Exception as e:
            return VerifyDocument(
                success=False,
                message=f"Verification failed: {str(e)}",
                result='error',
                details={'error': str(e)}
            )


class RequestAdditionalSignature(graphene.Mutation):
    """Allow the latest signatory to request additional signature from another user"""
    class Arguments:
        request_id = graphene.ID(required=True)
        signer_email = graphene.String(required=True)
        role = graphene.String(default_value='signer')
        require_all_signatures = graphene.Boolean(required=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    possible_signer = graphene.Field(PossibleSignerType)
    
    @staticmethod
    def mutate(root, info, request_id, signer_email, role='signer', require_all_signatures=False):
        user = info.context.user
        if not user.is_authenticated:
            return RequestAdditionalSignature(
                success=False,
                message="Authentication required",
                possible_signer=None
            )
        
        try:
            # Get the signing request
            signing_request = Request.objects.get(id=request_id)
            
            # Check if user is the latest signatory
            latest_sign = signing_request.signs.order_by('-signed_at').first()
            if not latest_sign or latest_sign.signer != user:
                return RequestAdditionalSignature(
                    success=False,
                    message="Only the latest signatory can request additional signatures",
                    possible_signer=None
                )
            
            # Find the user to add as signer
            try:
                new_signer = User.objects.get(email=signer_email)
            except User.DoesNotExist:
                return RequestAdditionalSignature(
                    success=False,
                    message=f"User with email {signer_email} not found",
                    possible_signer=None
                )
            
            # Check if user is already a possible signer
            existing = PossibleSigner.objects.filter(
                request=signing_request,
                signer=new_signer
            ).first()
            
            if existing:
                return RequestAdditionalSignature(
                    success=False,
                    message="User is already added as a possible signer",
                    possible_signer=existing
                )
            
            # Add the new possible signer
            possible_signer = PossibleSigner.objects.create(
                request=signing_request,
                signer=new_signer,
                role=role
            )
            
            # Update request status to pending if it was completed
            if signing_request.status == 'completed':
                signing_request.status = 'pending'
                signing_request.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='request_additional_signature',
                details={
                    'request_id': str(request_id),
                    'new_signer': new_signer.username,
                    'role': role
                }
            )
            
            return RequestAdditionalSignature(
                success=True,
                message=f"Successfully requested signature from {new_signer.username}",
                possible_signer=possible_signer
            )
            
        except Request.DoesNotExist:
            return RequestAdditionalSignature(
                success=False,
                message="Signing request not found",
                possible_signer=None
            )
        except Exception as e:
            return RequestAdditionalSignature(
                success=False,
                message=f"Error: {str(e)}",
                possible_signer=None
            )


class DocumentQuery(graphene.ObjectType):
    """Document Queries"""
    document = graphene.Field(DocumentType, id=graphene.ID(required=True))
    my_documents = graphene.List(DocumentType)
    all_documents = graphene.List(DocumentType)
    my_signing_requests = graphene.List(RequestType)
    my_signatures = graphene.List(SignatureType)
    pending_signatures = graphene.List(PossibleSignerType)
    signed_documents = graphene.List(RequestType)
    signing_request = graphene.Field(RequestType, id=graphene.ID(required=True))
    requests_awaiting_my_signature = graphene.List(RequestType)
    def resolve_document(self, info, id):
        try:
            return Document.objects.get(pk=id)
        except Document.DoesNotExist:
            return None
    
    def resolve_my_documents(self, info):
        user = info.context.user
        if user.is_authenticated:
            from django.db.models import Q
            # Get documents user uploaded OR documents where user is a possible signer
            return Document.objects.filter(
                Q(uploaded_by=user) | 
                Q(reqs__poss_signers__signer=user)
            ).distinct()
        return []
    
    def resolve_all_documents(self, info):
        user = info.context.user
        if user.is_authenticated and user.is_staff:
            return Document.objects.all()
        return []
    
    def resolve_my_signing_requests(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Request.objects.filter(requester=user)
        return []

    def resolve_my_signatures(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Signature.objects.filter(owner=user)
        return []
    
    def resolve_pending_signatures(self, info):
        user = info.context.user
        if user.is_authenticated:
            return PossibleSigner.objects.filter(
                signer=user,
                request__status='pending'
            )
        return []
    
    def resolve_signed_documents(self, info):
        user = info.context.user
        if user.is_authenticated:
            # Get all signing requests where the user has signed
            return Request.objects.filter(
                signs__signer=user
            ).distinct().order_by('-signs__signed_at')
        return []
    
    def resolve_signing_request(self, info, id):
        try:
            return Request.objects.get(pk=id)
        except Request.DoesNotExist:
            return None
    
    def resolve_requests_awaiting_my_signature(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Request.objects.filter(poss_signers__signer=user, status='pending').distinct()
        return []
class DocumentMutation(graphene.ObjectType):
    """All Document Mutations"""
    upload_document = UploadDocument.Field()
    create_signature = CreateSignature.Field()
    create_signing_request = CreateSigningRequest.Field()
    sign_document = SignDocument.Field()
    verify_document = VerifyDocument.Field()
    request_additional_signature = RequestAdditionalSignature.Field()

