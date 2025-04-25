const modalUtils = {
    imageModal: document.getElementById("imageModal"),
    modalImg: document.getElementById("modalImage"),
    detailsModal: document.getElementById("detailsModal"),
    images: [],
    currentImageIndex: 0,
	
	setup: function () {
        this.imageModal = document.getElementById("imageModal");
        this.modalImg = document.getElementById("modalImage");
        this.detailsModal = document.getElementById("detailsModal");

        // Reset currentImageIndex and images if needed
        if (this.imageModal) {
            const dataImages = this.imageModal.getAttribute("data-images");
            this.images = dataImages ? JSON.parse(dataImages) : [];
        }
		
		window.onclick = function(event) {
			if (event.target === modalUtils.detailsModal) {
				modalUtils.close_details_modal();
			} else if (event.target === modalUtils.imageModal) {
				modalUtils.close_image_modal();
			}
		};
    },
	
    open_image_modal: function () {
        modalUtils.imageModal.style.display = "block";
        modalUtils.modalImg.src = "/static/" + modalUtils.images[modalUtils.currentImageIndex];
    },
	
    close_image_modal: function () {
        modalUtils.imageModal.style.display = "none";
    },
	
    change_image: function (direction) {
        if (modalUtils.images.length > 0) {
            modalUtils.currentImageIndex += direction;
            if (modalUtils.currentImageIndex < 0) {
                modalUtils.currentImageIndex = modalUtils.images.length - 1;
            } else if (modalUtils.currentImageIndex >= modalUtils.images.length) {
                modalUtils.currentImageIndex = 0;
            }
            modalUtils.update_modal_image();
        }
    },
	
    update_modal_image: function () {
        if (modalUtils.modalImg && modalUtils.images[modalUtils.currentImageIndex]) {
            modalUtils.modalImg.src = `/static/${modalUtils.images[modalUtils.currentImageIndex]}`;
        }
    },
	
    open_details_modal: function () {
        modalUtils.detailsModal.style.display = "block";
    },
	
    close_details_modal: function () {
        modalUtils.detailsModal.style.display = "none";
    }
};

// Initialize modalUtils after DOM content is loaded
document.addEventListener("DOMContentLoaded", function () {
    modalUtils.setup();
});

// Expose specific methods globally
window.open_image_modal = modalUtils.open_image_modal.bind(modalUtils);
window.close_image_modal = modalUtils.close_image_modal.bind(modalUtils);
window.change_image = modalUtils.change_image.bind(modalUtils);
window.open_details_modal = modalUtils.open_details_modal.bind(modalUtils);
window.close_details_modal = modalUtils.close_details_modal.bind(modalUtils);