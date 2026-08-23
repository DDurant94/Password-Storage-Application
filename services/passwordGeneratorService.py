from utils.genorators import password_gen


class PasswordGeneratorService:
	"""Encapsulates password generation behind an injectable collaborator."""

	def __init__(self, generator=None):
		self._generator = generator or password_gen

	def generate(self):
		return self._generator()


password_generator_service = PasswordGeneratorService()


def generate():
	return password_generator_service.generate()
